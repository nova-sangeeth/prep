# Design a Chat System (WhatsApp / Messenger)

## 1. Requirements
- **Functional:**
  - 1:1 and group messaging; text + media.
  - Online/last-seen **presence**.
  - **Delivery and read receipts** (sent / delivered / read).
  - Offline delivery — store messages and deliver when the recipient reconnects.
  - **Push notifications** when the app is backgrounded/offline.
  - Per-conversation message **ordering**.
- **Non-functional:**
  - **Scale:** ~1B users, hundreds of millions concurrently connected, tens of billions of messages/day.
  - **Latency:** message send→deliver p99 < 500ms when both online; presence/typing near-real-time.
  - **Availability:** very high — chat is expected to "just work."
  - **Consistency:** per-conversation ordering and exactly-once *display* (dedup) matter; global ordering does not.
  - **Durability:** an accepted message must never be lost until delivered (and per retention policy after).

## 2. Back-of-envelope estimates
- **DAU ≈ 500M**, **~50M concurrent connections** at peak.
- **Messages:** 50B/day ≈ **580k msg/s**, peak ~1.5M/s.
- **Connections:** 50M persistent WebSockets. A tuned server holds ~100k-1M sockets → need **~50-500 gateway servers** just for connection termination (memory/FD bound, not CPU).
- **Storage:** 50B/day × ~300 bytes (text msg + metadata) ≈ **15 TB/day** before media. Media goes to blob storage + CDN, messages carry only a reference. With retention this is petabytes/yr → must shard and tier.
- **Presence fan-out:** if each online user has ~100 contacts and presence changes are broadcast, naive presence updates can dwarf message traffic — must be throttled/pulled (see deep dive).

## 3. API
```
WebSocket (client <-> gateway), message frames:
  SEND      { clientMsgId, convId, body, mediaRef? }
  ACK       { msgId, status: SERVER_RECEIVED|DELIVERED|READ }
  RECEIVE   { msgId, convId, senderId, body, ts }
  PRESENCE  { userId, status: ONLINE|OFFLINE|LASTSEEN, ts }
  TYPING    { convId, userId }

REST (control plane):
  GET /conversations/{id}/messages?cursor   -> history (paginated)
  POST /groups { members[] } ; POST /groups/{id}/members
```

## 4. High-level design
```
   phone == WebSocket ==> +------------------+
                          | Chat Gateway     |  (stateful: holds the socket)
                          |  (conn server)   |
                          +---------+--------+
                                    | who is `to`? which gateway?
                          +---------v--------+
                          | Session Registry | (userId -> gatewayId, in Redis)
                          +---------+--------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
       +------v------+      +-------v------+      +-------v-------+
       | Message Svc |----->| Message Store |     | Push Service  |
       | (persist,   |      | (sharded NoSQL)|     | APNs / FCM    |
       |  route, seq)|      +---------------+      +---------------+
       +------+------+
              | enqueue per-recipient
       +------v------+
       |  Outbox /   |  (offline queue per user, drained on reconnect)
       |  Kafka      |
       +-------------+
```
- **Chat Gateway:** terminates the persistent WebSocket; **stateful** (the connection lives here). Maps user↔socket.
- **Session Registry (Redis):** `userId -> gatewayId` so the system can find which gateway holds a recipient's live connection.
- **Message Service:** persists the message (durability first), assigns per-conversation sequence, routes to the recipient's gateway or to the offline queue.
- **Message Store:** durable, sharded by conversation/user.
- **Push Service:** sends APNs/FCM notifications when the recipient has no live socket.

## 5. Data model & storage choice
```
messages (partition key = conv_id, clustering key = seq/msg_id)
  conv_id, seq (per-conv monotonic), msg_id (Snowflake),
  sender_id, body, media_ref, created_at, status

conversations
  conv_id, type(1:1|group), member_ids[], last_msg_id

inbox / per-user offline queue (key = user_id)
  list of undelivered msg_ids

presence (Redis, key = user_id) -> { status, lastSeen, ttl }
session (Redis, key = user_id) -> gatewayId
```
**Choices:**
- **Messages:** **wide-column NoSQL (Cassandra/HBase)** partitioned by `conv_id`. Chat is write-heavy, append-only, and read as time-ordered ranges within a conversation — exactly the LSM/wide-column sweet spot. The clustering key gives ordered history reads and cheap pagination.
- **Presence & sessions:** **Redis** — ephemeral, high-churn, TTL-based, read on every routing decision.
- **Media:** blob store (S3) + CDN; messages store only a reference, keeping the message store small and fast.

## 6. Deep dives

### Connection management & routing
- Persistent **WebSocket** (falls back to long-poll) gives bidirectional, low-overhead delivery vs polling. Gateways are **stateful** — losing a gateway drops its sockets; clients auto-reconnect (possibly to a different gateway) and re-register in the Session Registry.
- **Routing a message:** Message Service looks up the recipient in the Session Registry → if online, forward to that gateway, which writes to the socket. If the recipient sits on another gateway, gateways communicate via an internal bus/RPC. If offline, enqueue.

### Message ordering & exactly-once display
- **Per-conversation sequence number** (assigned by the Message Service / the conv's shard) gives a total order *within a conversation* — enough for correct display; we don't need global ordering.
- Client sends a **clientMsgId**; the server dedups on it so retries (over flaky networks) don't create duplicates → **at-least-once delivery + idempotent display = effectively exactly-once** to the user.
- Client reorders by seq on receipt, so out-of-order network delivery still renders correctly.

### Delivery & read receipts
- Three states tracked per message: **sent** (server persisted), **delivered** (recipient's device ACKed receipt), **read** (recipient opened the chat). Each transition is a small ACK frame flowing back through the gateway to the sender. Group receipts aggregate per-member delivered/read state (more expensive — store per-member status or counts).

### Offline delivery & push
- If recipient offline, the message is persisted and added to their **per-user offline queue/inbox**. On reconnect, the gateway drains the queue in seq order and the client ACKs. In parallel, the **Push Service** fires an APNs/FCM notification so the user knows to open the app. Push is best-effort and out-of-band; the durable queue is the real guarantee.

### Presence (the scaling trap)
- Naive "broadcast every status change to all contacts" explodes: an online user with N contacts × frequent flaps = quadratic fan-out. Mitigations:
  - **Heartbeat + TTL:** client sends periodic heartbeats; presence key in Redis has a TTL → missing heartbeats ⇒ offline, no explicit "offline" message needed.
  - **Pull / on-demand:** fetch presence for contacts only when a chat list is visible, rather than pushing every change.
  - **Debounce/throttle** rapid online↔offline flapping; coalesce updates.

## 7. Bottlenecks & scaling
- **First to break: connection capacity & gateway memory** — millions of idle sockets. Fix: horizontal gateways, FD/memory tuning, and offloading idle connections; gateways are stateless about *content* (state is in Redis/store) so they scale out freely.
- **Presence fan-out** is the classic killer — solve with heartbeat+TTL and pull, not broadcast.
- **Hot conversations / large groups:** a 100k-member group turns one send into 100k deliveries → treat huge groups like fan-out-on-read (members pull) or batch deliveries; cap group size.
- **Message store hot partitions:** shard by conv_id; very active conversations may need sub-partitioning by time bucket.
- **Thundering reconnect** after a gateway dies → jittered backoff on clients, spread reconnects.
- **Push throughput:** APNs/FCM rate limits → batch and prioritize.

## 8. Tradeoffs / talking points
- Persistent WebSockets (stateful gateways) beat polling for latency but make the gateway tier stateful — push all durable state into Redis/store so gateways stay replaceable.
- Per-conversation ordering via sequence numbers is sufficient and far cheaper than global ordering.
- At-least-once delivery + client-side dedup on clientMsgId = exactly-once *display* without expensive distributed consensus.
- Durable offline queue is the delivery guarantee; push notifications are best-effort and out-of-band.
- Presence is deceptively expensive — heartbeat+TTL+pull instead of broadcast is the key insight.
- Media via CDN with references keeps the message store lean and the hot path fast.

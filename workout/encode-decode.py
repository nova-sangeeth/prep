def encode(s: str) -> str:
    """
    Encode the string
    """
    result = ""
    for word in s.split():
        # Construct the encoded string

        result += str(len(word)) + "#" + word
    return result


def decode(data: str) -> str:
    """
    Decode the string
    """
    result =[]
    i = 0
    while i < len(data):
        j = i
        while data[j] != "#":
            j += 1
        
        limit = int(data[i:j])
        start = j + 1
        end = limit + start
        word = data[start:end]

        result.append(word)
        i = end
        
    return result


def main() -> None:

    sentence = "The quick brown fox jumps over the lazy dog"

    # encoded_sentence = "3#The5#quick5#brown3#fox5#jumps4#over3#the4#lazy3#dog"
    # print(encoded_sentence[2:2 + 3])
    encoded_string = encode(s=sentence)
    print(encoded_string)
    decoded_string = decode(data=encoded_string)
    print(decoded_string)


if __name__ == "__main__":
    main()

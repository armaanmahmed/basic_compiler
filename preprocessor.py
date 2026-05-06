from sys import argv

DEFINE_TEXT = "#define "
SINGLE_LINE_COMMENT_TEXT = "//"


def _extract_mappings(raw_text_str: str) -> tuple[list[str], dict[str, str]]:
    mappings = {}
    text_lines = []

    # pass one: load in mappings
    for line in raw_text_str.splitlines():
        if line.startswith(DEFINE_TEXT):
            # convert from '#define  key value' -> 'key value'
            stripline = line.removeprefix(DEFINE_TEXT).strip()
            sep_idx = stripline.find(" ")

            # mappings[key] = value
            if sep_idx != -1:
                mappings[stripline[:sep_idx]] = stripline[sep_idx:].strip()
        else:
            text_lines.append(line)

    return mappings, text_lines


def _process_macros(raw_text_lines: list[str], macro_map: dict[str, str]):
    processed_lines = []

    for line in raw_text_lines:
        # prevent infinite substitutions - may update based on actual preprocessor behavior
        loop_check = set()
        processed_line = line

        # while this line contains any macros not in the already-replaced set
        while any(processed_line.find(key) != -1 for key in macro_map if key not in loop_check):
            for key, value in macro_map.items():
                if processed_line.find(key) != -1:
                    processed_line = processed_line.replace(key, value)

        # once fully processed, add the line to the list
        processed_lines.append(processed_line)

    return "\n".join(processed_lines)


def preprocess(raw_text: str, debug=False):
    # pass one: extract macros
    mappings, lines_without_defines = _extract_mappings(raw_text)

    if debug:
        print(f'mappings: {mappings}')
        print(f'lines without defines: {lines_without_defines}')

    # pass two: process macros
    processed_text = _process_macros(lines_without_defines, mappings)

    # pass three: remove comments
    lines_without_comments: list[str] = []
    for line in processed_text.splitlines():
        comment_idx = line.find(SINGLE_LINE_COMMENT_TEXT)
        if comment_idx == -1:
            lines_without_comments.append(line)
        else:
            lines_without_comments.append(line[:comment_idx])

    return "\n".join((l for l in lines_without_comments if l.strip()))


if __name__ == "__main__":
    if len(argv) < 2:
        filename = input("Enter a file: ")
    else:
        filename = argv[1]

    with open(filename, 'r') as file:
        preprocessed_text = preprocess(file.read())
        print(preprocessed_text)

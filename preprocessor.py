import re
from dataclasses import dataclass
from sys import argv

# macros for the preprocessor
DEFINE_TEXT = "#define "
SINGLE_LINE_COMMENT_TEXT = "//"
MULTI_LINE_COMMENT_BEGIN = "/*"
MULTI_LINE_COMMENT_END = "*/"
TARGET_DIR = "target_files/"
MACRO_FN_DEF_REGEX = r"(\w+)(\((.*?)\))?\s+(.*)"
# regex matches macro name (1), then optional parens and args (2, 3),
# and then optional whitespace and the body (4)

# some classes for organization


@dataclass
class Macro:
    body: str
    args: list[str] | None = None


class CommentParseException(Exception):
    pass


class MacroParseException(Exception):
    pass


class Preprocessor:
    def __init__(self, src: str):
        self.src = src

    def _remove_comments(self, text: str) -> str:
        lines_without_multiline_comments: list[str] = []
        in_multiline_comment = False

        # strip out multiline comments
        for line in text.splitlines():
            # handles the case of multiple multiline comments in a single line
            line_frags = []
            left_to_parse = line

            # iterate through and case on whether in multiline comment
            # and the presence of the next comment start/end symbol
            while left_to_parse:
                if not in_multiline_comment:
                    cut_start_idx = left_to_parse.find(MULTI_LINE_COMMENT_BEGIN)

                    # if no multiline comment marker found, simply append and advance
                    if cut_start_idx == -1:
                        line_frags.append(left_to_parse)
                        break
                    else:
                        # if found, append everything until then and cut the marker too
                        in_multiline_comment = True
                        line_frags.append(left_to_parse[:cut_start_idx])
                        left_to_parse = left_to_parse[
                            cut_start_idx + len(MULTI_LINE_COMMENT_BEGIN) :
                        ]
                else:
                    cut_end_idx = left_to_parse.find(MULTI_LINE_COMMENT_END)
                    # if not found, then everything else is comment so can be discarded
                    if cut_end_idx == -1:
                        break
                    else:
                        left_to_parse = left_to_parse[
                            cut_end_idx + len(MULTI_LINE_COMMENT_END) :
                        ]
                        in_multiline_comment = False

            lines_without_multiline_comments.append("".join(line_frags))

        if in_multiline_comment:
            raise CommentParseException("Unpaired multiline comment syntax")

        lines_without_comments: list[str] = []

        # strip out single line comments
        for line in lines_without_multiline_comments:
            comment_idx = line.find(SINGLE_LINE_COMMENT_TEXT)
            if comment_idx == -1:
                lines_without_comments.append(line)
            else:
                lines_without_comments.append(line[:comment_idx])

        text_without_comments = "\n".join(
            l for l in lines_without_comments if l.strip()
        )

        return text_without_comments

    def _extract_mappings(self, raw_text_str: str) -> list[str]:
        mappings: dict[str, Macro] = {}
        text_lines: list[str] = []

        for line in raw_text_str.splitlines():
            if line.startswith(DEFINE_TEXT):
                # convert from '#define  key value' -> 'key value'
                stripline = line.removeprefix(DEFINE_TEXT).strip()

                match = re.search(MACRO_FN_DEF_REGEX, stripline)
                if match is None:
                    raise MacroParseException(f"Malformed macro definition: {line}")
                key, fmatch, args, body = match.groups()
                if fmatch is not None:
                    macro = Macro(body, [arg.strip() for arg in args.split(",")])
                else:
                    macro = Macro(body)
                mappings[key] = macro
            else:
                text_lines.append(line)

        self.macro_map = mappings
        return text_lines

    def _find_macro_call(
        self, line: str, key: str, start: int = 0
    ) -> tuple[int, int, list[str]] | None:
        # track parentheses depth for nested function calls
        call_start = line.find(key + "(", start)
        if call_start == -1:
            return None

        depth = 0
        args: list[str] = []
        current_arg: list[str] = []

        for i in range(call_start + len(key), len(line)):
            char = line[i]
            if char == "(":
                depth += 1

                # this is the top-level call, ( is not part of an arg
                if depth == 1:
                    continue
            elif char == ")":
                depth -= 1
                if depth == 0:
                    args.append("".join(current_arg).strip())
                    return call_start, i + 1, args

            # commas separate arguments at the top level
            elif char == "," and depth == 1:
                args.append("".join(current_arg).strip())
                current_arg = []
                continue

            current_arg.append(char)

        # loop can only exhaust without returning if parens never rebalanced
        raise MacroParseException(f"Unbalanced parentheses in call to {key}")

    # prevent infinite substitutions
    def _eval_line(self, line: str, expanded_macros: set[str] | None = None) -> str:
        if expanded_macros is None:
            expanded_macros = set()
        processed_line = line

        # substitute any macros not in the already-replaced set
        for key, macro in self.macro_map.items():
            if key in expanded_macros:
                continue

            # divide into function and object cases based on macro.args
            if macro.args is None:
                # object case
                if key in processed_line:
                    expanded_body = self._eval_line(
                        macro.body, expanded_macros.union({key})
                    )
                    processed_line = processed_line.replace(key, expanded_body)
            else:
                # function case
                search_from = 0
                while (
                    call := self._find_macro_call(processed_line, key, search_from)
                ) is not None:
                    call_start, call_end, call_args = call
                    if len(call_args) != len(macro.args):
                        raise MacroParseException(
                            f"Number of arguments for {key} do not match: "
                            f"args were {call_args} at call site and "
                            f"{macro.args} at definition site"
                        )

                    # expand the args first
                    expanded_args = [
                        self._eval_line(arg, expanded_macros) for arg in call_args
                    ]

                    # substitute argument by argument, on whole words only
                    # so an arg named x doesn't overwrite names containing x
                    body_with_args = macro.body
                    for macro_arg, call_arg in zip(macro.args, expanded_args):
                        body_with_args = re.sub(
                            rf"\b{macro_arg}\b", call_arg, body_with_args
                        )

                    # the substituted body may not use itself
                    # add the macro to expanded_macros
                    expanded_body = self._eval_line(
                        body_with_args, expanded_macros.union({key})
                    )

                    processed_line = (
                        processed_line[:call_start]
                        + expanded_body
                        + processed_line[call_end:]
                    )
                    search_from = call_start + len(expanded_body)

        return processed_line

    def _process_macros(self, raw_text_lines: list[str]):
        return [self._eval_line(line) for line in raw_text_lines]

    def preprocess(self):
        # pass one: remove comments
        lines_without_comments = self._remove_comments(self.src)

        # pass two: extract macro mappings
        lines_without_defines = self._extract_mappings(lines_without_comments)

        # pass three: process macros
        substituted_text_lines = self._process_macros(lines_without_defines)
        full_text = "\n".join(substituted_text_lines)

        return full_text


if __name__ == "__main__":
    if len(argv) < 2:
        filename = TARGET_DIR + input("Enter a file: ")
    else:
        filename = argv[1]

    with open(filename, "r") as file:
        preprocessor = Preprocessor(file.read())
        preprocessed_text = preprocessor.preprocess()
        print(preprocessed_text)

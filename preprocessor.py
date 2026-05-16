from dataclasses import dataclass
from sys import argv
import re

# macros for the preprocessor
DEFINE_TEXT = "#define "
SINGLE_LINE_COMMENT_TEXT = "//"
MULTI_LINE_COMMENT_BEGIN = "/*"
MULTI_LINE_COMMENT_END = "*/"
TARGET_DIR = "target_files/"
MACRO_FN_DEF_REGEX = r'(\w+)(\((.*?)\))?\s+(.*)'
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
                    cut_start_idx = left_to_parse.find(
                        MULTI_LINE_COMMENT_BEGIN)

                    # if no multiline comment marker found, simply append and advance
                    if cut_start_idx == -1:
                        line_frags.append(left_to_parse)
                        break
                    else:
                        # if found, append everything until then and cut the marker too
                        in_multiline_comment = True
                        line_frags.append(left_to_parse[:cut_start_idx])
                        left_to_parse = left_to_parse[cut_start_idx +
                                                      len(MULTI_LINE_COMMENT_BEGIN):]
                else:
                    cut_end_idx = left_to_parse.find(MULTI_LINE_COMMENT_END)
                    # if not found, then everything else is comment so can be discarded
                    if cut_end_idx == -1:
                        break
                    else:
                        left_to_parse = left_to_parse[cut_end_idx +
                                                      len(MULTI_LINE_COMMENT_END):]
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
            (l for l in lines_without_comments if l.strip())
        )

        return text_without_comments

    def _extract_mappings(self, raw_text_str: str) -> tuple[list[str], dict[str, Macro]]:
        mappings: dict[str, Macro] = {}
        text_lines: list[str] = []

        for line in raw_text_str.splitlines():
            if line.startswith(DEFINE_TEXT):
                # convert from '#define  key value' -> 'key value'
                stripline = line.removeprefix(DEFINE_TEXT).strip()

                match = re.search(MACRO_FN_DEF_REGEX, stripline)
                key, fmatch, args, body = match.groups()
                if fmatch is not None:
                    macro = Macro(body, args.split(","))
                else:
                    macro = Macro(body)
                mappings[key] = macro
            else:
                text_lines.append(line)

        return mappings, text_lines

    def _process_macros(self, raw_text_lines: list[str], macro_map: dict[str, Macro]):
        processed_lines = []

        for line in raw_text_lines:
            # prevent infinite substitutions
            loop_check = set()
            processed_line = line

            # while this line contains any macros not in the already-replaced set
            while any(key in processed_line for key in macro_map if key not in loop_check):
                for key, macro in macro_map.items():
                    if key in processed_line:
                        # divide into function and object cases based on macro.args
                        if macro.args is None:
                            processed_line = processed_line.replace(
                                key, macro.body)
                        else:
                            for match in re.finditer(rf'{key}\((.*?)\)', processed_line):
                                call_args = match.group(1).split(",")
                                if len(call_args) != len(macro.args):
                                    raise MacroParseException(
                                        (f"Number of arguments for {key} do not match: "
                                         f"args were {call_args} at call site and "
                                         f"{macro.args} at definition site")
                                    )
                                body_with_args = macro.body

                                # substitute argument by argument
                                for macro_arg, call_arg in zip(macro.args, call_args):
                                    body_with_args = body_with_args.replace(
                                        macro_arg, call_arg)

                                processed_line = processed_line.replace(
                                    match.group(0), body_with_args
                                )

                        loop_check.add(key)

            # once fully processed, add the line to the list
            processed_lines.append(processed_line)

        return processed_lines

    def preprocess(self):
        # pass one: remove comments
        lines_without_comments = self._remove_comments(self.src)

        # pass two: extract macro mappings
        mappings, lines_without_defines = self._extract_mappings(
            lines_without_comments)

        # pass three: process macros
        substituted_text_lines = self._process_macros(
            lines_without_defines, mappings)
        full_text = "\n".join(substituted_text_lines)

        return full_text


if __name__ == "__main__":
    if len(argv) < 2:
        filename = TARGET_DIR + input("Enter a file: ")
    else:
        filename = argv[1]

    with open(filename, 'r') as file:
        preprocessor = Preprocessor(file.read())
        preprocessed_text = preprocessor.preprocess()
        print(preprocessed_text)

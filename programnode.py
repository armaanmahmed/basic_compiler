from dataclasses import dataclass


@dataclass
class ProgramNode:
    """A list of children of this ProgramNode"""
    children: list["ProgramNode"]

"""
Create arrow waypoints according to grid in `input.json` specification dicts
Arrows are represented by strings according to `DirectionKeys` and `ArrowDirections` below.
"""

import os
import re
import json
import math
import typing
import warnings
from enum import Enum
from dataclasses import dataclass, asdict, astuple


class PointDict(typing.TypedDict):
  x: float
  y: float

@dataclass
class Point():
  """2D point with vector operations."""
  
  x: float = 0
  y: float = 0
  
  def __add__(self, other: Point) -> Point:
    if not isinstance(other, Point):
      return NotImplemented
    return Point(self.x + other.x, self.y + other.y)
  
  def __sub__(self, other: Point) -> Point:
    if not isinstance(other, Point):
      return NotImplemented
    return Point(self.x - other.x, self.y - other.y)
  
  def __mul__(self, number: float) -> Point:
    return Point(self.x * number, self.y * number)
  
  def __round__(self, ndigits: int=0) -> Point:
    return Point(round(self.x, ndigits), round(self.y, ndigits))
  
  def length(self) -> float:
    return math.hypot(self.x, self.y)

  def normalise(self) -> Point:
    """Return a direction vector with unit length."""

    length = self.length()
    if length == 0:
      raise ValueError("Cannot normalise a zero-length vector")
    return Point(self.x / length, self.y / length)
  
  def transpose(self) -> Point:
    return Point(self.y, self.x)


class DirectionKeys(Enum):
  """Nine keys representing cardinal directions, ordered in a clockwise spiral as per a qwerty layout:
    +---------------+
    | q:8  w:1  e:2 |
    |               |
    | a:7  s:0  d:3 |
    |               |
    | z:6  x:5  c:4 |
    +---------------+
  """

  S = "s"
  W = "w"
  E = "e"
  D = "d"
  C = "c"
  X = "x"
  Z = "z"
  A = "a"
  Q = "q"


class ArrowDirections(Enum):
  """Nine cardinal directions corresponding to the nine `DirectionKeys`."""

  CENTRE = (0, 0)
  NORTH = (0, -1)
  NORTH_EAST = (1, -1)
  EAST = (1, 0)
  SOUTH_EAST = (1, 1)
  SOUTH = (0, 1)
  SOUTH_WEST = (-1, 1)
  WEST = (-1, 0)
  NORTH_WEST = (-1, -1)

  @classmethod
  def from_key(cls, key: str | DirectionKeys) -> ArrowDirections | None:
    """Convert direction key (s|w|e|d|c|x|z|a|q) to enum."""

    try:
      if type(key) is not DirectionKeys:
        key = DirectionKeys(key)
    except ValueError:
      warnings.warn(f"'{key}' is not a valid DirectionKeys value")
      return None
  
    return list(ArrowDirections)[list(DirectionKeys).index(key)]

  @classmethod
  def from_keys(cls, keys: typing.Iterable[str | DirectionKeys]) -> list[ArrowDirections | None]:
    """Convert an iterable of direction keys."""

    return [ArrowDirections.from_key(key) for key in keys]
  
  def get_point(self) -> Point:
    return Point(*self.value)
  
  @classmethod
  def from_point(cls, point: Point) -> ArrowDirections:
    return ArrowDirections(astuple(round(point.normalise())))


class SpecificationDict(typing.TypedDict):
  colour: str
  grid: list[list[str]]

class CellSpecification:
  """Parses arrow specification strings into a list of specification tuples."""

  def __init__(self, cell_position: Point, specification_string: str):
    self.cell_position = cell_position
    self.injest_specification_string(specification_string)

  def get_bent_tip(self, bent_arrow_directions: list[ArrowDirections]):
    tip_position = bent_arrow_directions[-1]
    tip_direction = ArrowDirections.from_point(
      tip_position.get_point() - bent_arrow_directions[-2].get_point())
    return (tip_position, tip_direction)
  
  def expand_shorthand(self, specification_string: str) -> str:
    """Expands shorthand variants of specification string tokens:
      Small: "w" -> "w:w", "wd:axq" -> "w:wd:ax:xq:q"
      Bent: "{wd}" -> "{wwd}" """
    
    # Pattern: any char not preceded/followed by colon or within braces gets duplicated around a colon
    expand_small = lambda string: re.sub(r'(?<!:)(\w)(?!:|\w*\})', r'\1:\1', string)

    #  Pattern: the first of two chars within braces gets duplicated
    expand_bent = lambda string: re.sub(r'(?<=\{)(\w)(?=\w\})', r'\1\1', string)

    return expand_small(expand_bent(specification_string))

  def injest_specification_string(self, specification_string: str):
    """Extracts specification tokens from specification_string and transforms
    them into a list of arrow specifications line specifications."""

    self.arrows: list[tuple[ArrowDirections, ArrowDirections]] = []
    self.lines: list[list[ArrowDirections]] = []
    for token_match in re.finditer(
        r'(?P<small>\w:\w)|(?:\{(?P<bent>\w+)\})',
        self.expand_shorthand(specification_string)):
      match { name: value
              for name, value in token_match.groupdict().items()
              if value is not None }:
        case { 'small': specification }:
          position, direction = ArrowDirections.from_keys(specification.split(':'))
          self.arrows.append((position, direction))
        case { 'bent': specification }:
          directions = ArrowDirections.from_keys(specification)
          self.lines.append(directions)
          self.arrows.append(self.get_bent_tip(directions))


class GridSpecifications:
  """Implements the ability to iterate a list[ArrowSpecification]."""

  def __init__(self, input_data: list[SpecificationDict]):
    self.specifications = {
      specification_dict["colour"]: [
        CellSpecification(
          Point(column_index, row_index),
          specification_string)
        for row_index, row in enumerate(specification_dict["grid"])
        for column_index, specification_string in enumerate(row)]
      for specification_dict in input_data }
  
  def __iter__(self) -> typing.Generator[tuple[str, CellSpecification], None, None]:
    for colour, cell_specifications in self.specifications.items():
      yield (colour, cell_specifications)


class ArrowGeometryDict(typing.TypedDict):
  arrow_waypoints: dict[DirectionKeys, list[PointDict]]
  arrow_positions: dict[DirectionKeys, PointDict]
  side_positions: dict[DirectionKeys, PointDict]

class ArrowGeometry:
  """Injest arrow_geometry.json as `Point` based dicts."""

  def __init__(self, data: ArrowGeometryDict):
    self.waypoints = {
      ArrowDirections.from_key(key): [
        Point(**waypoint) for waypoint in waypoints]
      for key, waypoints in data["arrow_waypoints"].items()}
    
    self.points = {
      ArrowDirections.from_key(key): Point(**point)
      for key, point in data["arrow_positions"].items()}
    
    self.side_points = {
      ArrowDirections.from_key(key): Point(**point)
      for key, point in data["side_positions"].items()}


class ArrowGenerator:
  """Generates arrow path data for Sudoku Maker from input.json specifications.
  Handles both simple arrows ("small") and right-angle arrows "bent" with connecting lines."""

  ARROW_THICKNESS = 0.0265625
  LINE_THICKNESS = ARROW_THICKNESS + 0.05
  
  def __init__(self, arrow_geometry: ArrowGeometryDict, input_data: list[SpecificationDict]):
    self.geometry = ArrowGeometry(arrow_geometry)
    self.grid_specifications = GridSpecifications(input_data)
  
  def get_waypoints(self, position: ArrowDirections, direction: ArrowDirections) -> list[Point]:
    """Arrow waypoints are stored with the arrow pointing away from the centre of the cell.
    For an arrow not pointing away from the centre of the cell, we need to get the arrow pointing
    in the correct direction and offset it to the correct position."""

    if position == direction:
      return self.geometry.waypoints[direction]
    offset = self.geometry.points[position] - self.geometry.points[direction]
    return [waypoint + offset for waypoint in self.geometry.waypoints[direction]]
  
  def offset_waypoints(self, waypoints: list[Point], offset: Point) -> list[Point]:
    """Adds an offset to each waypoint.
    Used to transform positions within a cell to positions on the sudoku grid"""

    return [
      round(waypoint + offset, 3)
      for waypoint in waypoints]

  def make_arrows(self, specification: CellSpecification) -> list[list[Point]]:
    """Makes small arrows that are a series of SVG path points defining the shape of the arrow.
    Can be standalone as small arrows or function as the tip of bent arrows."""

    return [self.offset_waypoints(self.get_waypoints(position, direction), specification.cell_position)
            for position, direction in specification.arrows]
  
  def get_closest_side_point(self, line_point: Point, direction: Point) -> Point:
    """Get the closest side point to the point along direction.
    Only works if direction has a component equal to zero, otherwise will effectively project sidepoint from the centre."""

    return Point(*(
      round(line_value) if direction_value != 0 else line_value
      for line_value, direction_value in zip(*(
        asdict(point).values() for point in [line_point, direction]))))
  
  def get_line_points(self, positions: list[ArrowDirections]) -> list[Point]:
    """Gets three points defining a right angle from the centre of the side of the cell (offset) to the centre of the arrow tip."""

    points = [self.geometry.points[position] for position in positions]

    side_point = self.get_closest_side_point(points[0], (
      (positions[2].get_point() - positions[1].get_point()).normalise().transpose()
      if positions[0] == positions[1]
      else (points[0] - points[1]).normalise()))
    
    offset_side_point = side_point - (side_point - points[1]).normalise() * (self.LINE_THICKNESS / 2)
    return [offset_side_point, *points[1:]]
  
  def make_lines(self, specification: CellSpecification) -> list[list[Point]]:
    """Makes lines for body of bent arrows. Tip is an overlaid small arrow.
    Lines will use stroke rather than fill to draw the arrow body to avoid needing to handle curves."""

    return [
      self.offset_waypoints(self.get_line_points(positions), specification.cell_position)
      for positions in specification.lines]
  
  def collapse_xy_objects(self, json: str) -> str:
    """Corrects
        {
          "x": {x},
          "y": {y}
        }
    to
        { "x": {x}, "y": {y} }
    for JSON legibility"""

    return re.sub(
      r'\{\s+"x": ([0-9\.\-]+),\s+"y": ([0-9\.\-]+)\s+\}',
      r'{ "x": \1, "y": \2 }', json)
  
  def write_to_files(self):
    """Creates JSON output files containing SVG path coordinates"""

    for colour, cell_specifications in self.grid_specifications:
      base_path = f"output/{colour}"
      line_dict = {
        f"{base_path}/1-lines.json": (
          [waypoints
           for cell_specification in cell_specifications
           for waypoints in self.make_lines(cell_specification)],
          self.LINE_THICKNESS),
        f"{base_path}/2-arrows.json": (
          [waypoints
           for cell_specification in cell_specifications
           for waypoints in self.make_arrows(cell_specification)],
          self.ARROW_THICKNESS) }

      for path, (lines, thickness) in line_dict.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as output_file:
          output_file.writelines(
            self.collapse_xy_objects(json.dumps({
              "lines": [[asdict(point) for point in row] for row in lines],
              "style": { "thickness": thickness, "color": colour }
            }, indent=2)))


def read_file(path: str) -> typing.Any:
  with open(path, "r") as input_file:
    data = json.load(input_file)
  return data

def read_geometry() -> ArrowGeometryDict:
  return read_file("data/arrow_geometry.json")

def read_input() -> list[SpecificationDict]:
  return read_file("input.json")

def main():
  arrow_generator = ArrowGenerator(
    read_geometry(),
    read_input())
  
  arrow_generator.write_to_files()

if __name__ == "__main__":
  main()

"""
Create arrow waypoints according to grid in `input.json` specification dicts
Arrows are represented by strings according to:
  +-------+
  | q w e |
  | a   d |
  | z x c |
  +-------+
"""

import os
import re
import json
import math
import typing
from enum import IntEnum
from dataclasses import dataclass, asdict


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


DirectionKey = typing.Literal["w", "e", "d", "c", "x", "z", "a", "q", "s"]
ARROW_DIRECTIONS_KEY_ORDER: tuple[str] = typing.get_args(DirectionKey)[:-1]

class ArrowDirections(IntEnum):
  """Eight cardinal/ordinal directions numbered clockwise from north."""

  NORTH = 0
  NORTH_EAST = 1
  EAST = 2
  SOUTH_EAST = 3
  SOUTH = 4
  SOUTH_WEST = 5
  WEST = 6
  NORTH_WEST = 7

  @classmethod
  def from_key(cls, key: DirectionKey) -> ArrowDirections:
    """Convert direction key (w|e|d|c|x|z|a|q|s) to enum.
    's' is handled given the intuitive association from wasd."""

    return ArrowDirections(ARROW_DIRECTIONS_KEY_ORDER.index(
      "x" if key == "s" else key))


class SpecificationDict(typing.TypedDict):
  type: str
  colour: str
  grid: list[list[str]]

ArrowPoints = list[tuple[Point, ArrowDirections, ArrowDirections]]

class ArrowSpecification:
  """Parses grid-based arrow specifications into position/direction tuples."""

  def __init__(self, data: SpecificationDict):
    self.type_of_arrows = data["type"]
    self.colour = data["colour"]
    self.arrow_points = [
      (Point(column_index, row_index), position, direction)
      for row_index, row in enumerate(data["grid"])
      for column_index, directions in enumerate(row)
      for position, direction in self.split_directions(directions)]
    
  def split_directions(self, directions: str) -> list[list[ArrowDirections]]:
    """Expands shorthand `DirectionKey` representations:
        "w" -> "w:w", "wd:axq" -> "w:wd:ax:xq:q"""
    
    # Pattern: any char not preceded/followed by colon gets duplicated with colon
    expanded_directions = re.sub(r'(?<!:)([^:])(?!:)', r'\1:\1', directions)
    return [
      [ArrowDirections.from_key(direction)
       for direction in expanded_directions[index:index + 3].split(':')]
      for index in range(0, len(expanded_directions), 3)]

class ArrowSpecificationFactory:
  """Implements the ability to iterate a list[ArrowSpecification]."""

  def __init__(self, input_data: list[SpecificationDict]):
    self.specifications = [
      ArrowSpecification(specification_dict)
      for specification_dict in input_data]
  
  def __iter__(self) -> typing.Generator[tuple[str, str, ArrowPoints], None, None]:
    for specification in self.specifications:
      yield (specification.type_of_arrows,
             specification.colour,
             specification.arrow_points)


class ArrowGeometryDict(typing.TypedDict):
  arrow_waypoints: dict[DirectionKey, list[PointDict]]
  arrow_positions: dict[DirectionKey, PointDict]
  side_positions: dict[DirectionKey, PointDict]

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
    self.specifications = ArrowSpecificationFactory(input_data)
  
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

  def make_arrows(self, arrow_points: ArrowPoints) -> list[list[Point]]:
    """Makes small arrows that are a series of SVG path points defining the shape of the arrow.
    Can be standalone as small arrows or function as the tip of bent arrows."""

    return [self.offset_waypoints(self.get_waypoints(position, direction), cell_position)
            for cell_position, position, direction in arrow_points]
  
  def get_line_points(self, position: ArrowDirections, direction: ArrowDirections) -> tuple[Point, Point]:
    """Gets three points defining a right angle from the centre of the side of the cell (offset) to the centre of the arrow tip."""

    bend_position = ArrowDirections((2 * position.value - direction.value) % len(ArrowDirections))
    bend_point = self.geometry.points[bend_position]
    side_point = self.geometry.side_points[bend_position]
    offset_side_point = side_point - (side_point - bend_point).normalise() * (self.LINE_THICKNESS / 2)
    return (offset_side_point, bend_point)
  
  def make_lines(self, arrow_points: ArrowPoints) -> list[list[Point]]:
    """Makes lines for body of bent arrows. Tip is an overlaid small arrow.
    Lines will use stroke rather than fill to draw the arrow body to avoid needing to handle curves."""

    return [
      self.offset_waypoints([
        *self.get_line_points(position, direction),
        self.geometry.points[position]
      ], cell_position)
      for cell_position, position, direction in arrow_points]
  
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

    for type_of_arrows, colour, arrow_points in self.specifications:
      base_path = f"output/{type_of_arrows}/{colour}"
      match type_of_arrows:
        case "small":
          line_dict = { f"{base_path}.json": (
            self.make_arrows(arrow_points),
            self.ARROW_THICKNESS) }
        case "bent":
          line_dict = {
            f"{base_path}/1-lines.json": (
              self.make_lines(arrow_points),
              self.LINE_THICKNESS),
            f"{base_path}/2-arrows.json": (
              self.make_arrows(arrow_points),
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

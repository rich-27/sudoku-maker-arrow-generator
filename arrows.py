"""
Create arrow waypoints according to grid in `input.json` specification dicts
Arrows are represented by strings according to `DirectionKeys` and `ArrowDirections` below.
"""

import os
import re
import enum
import json
import math
import typing
import warnings
from types import MappingProxyType
from dataclasses import dataclass, asdict, astuple


@dataclass(frozen=True)
class Point():
  """Immutable 2D point with vector operations."""
  
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
  
  def perpendicular(self) -> Point:
    """Mirror a vector around the negative diagonal, `Point(0, 0) + t * Point(1, 1)`."""
    
    return Point(self.y, self.x)


class MetaEnum(enum.EnumMeta):
  """Metaclass for enabling `value in Enum` behaviour"""

  def __contains__(cls, item):
    try:
      cls(item)
    except ValueError:
      return False
    return True

class Enum(enum.Enum, metaclass=MetaEnum):
  """Base class for enabling `value in Enum` behaviour"""

  pass


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

    if not isinstance(key, DirectionKeys):
      if key not in DirectionKeys:
        warnings.warn(f"'{key}' is not a valid DirectionKeys value")
        return None
      key = DirectionKeys(key)
    
    return list(ArrowDirections)[list(DirectionKeys).index(key)]

  @classmethod
  def from_keys(cls, keys: typing.Iterable[str | DirectionKeys]) -> list[ArrowDirections | None]:
    """Convert an iterable of direction keys."""

    return [ArrowDirections.from_key(key) for key in keys]
  
  def get_point(self) -> Point:
    """Get a 2D vector for use in arithmetic."""
    
    return Point(*self.value)
  
  @classmethod
  def from_point(cls, point: Point) -> ArrowDirections:
    """Convert a 2D vector to its closest `ArrowDirections` approximation."""
    
    return ArrowDirections(astuple(round(point.normalise())))

class DoubleArrowDirections(Enum):
  """Four identifiers representing the four double arrow orientations"""

  VERTICAL = "v"
  POSITIVE_DIAGONAL = "p"
  HORIZONTAL = "h"
  NEGATIVE_DIAGONAL = "n"

  @classmethod
  def from_key(cls, key: str | DoubleArrowDirections) -> DoubleArrowDirections | None:
    """Convert key (v|p|h|n) to enum."""

    if not isinstance(key, DoubleArrowDirections):
      if key not in DoubleArrowDirections:
        return None
      key = DoubleArrowDirections(key)
    
    return key

  @classmethod
  def from_keys(cls, keys: typing.Iterable[str | DoubleArrowDirections]) -> list[DoubleArrowDirections | None]:
    """Convert an iterable of direction keys."""

    return [DoubleArrowDirections.from_key(key) for key in keys]


class JSONFileInjester:
  """Base class for classes that load a JSON file."""

  @staticmethod
  def read_file[T](filepath: str) -> T:
    with open(filepath, "r") as input_file:
      data = json.load(input_file)
    return data


"""Module level variable for use after instantiation in main."""
arrow_geometry: ArrowGeometry

class ArrowGeometry(JSONFileInjester):
  """Injest arrow_geometry.json as immutable `Point` based dicts."""

  def __init__(self, filepath: str):
    self.read_geometry_file(filepath)
  
  class _PointDict(typing.TypedDict):
    x: float
    y: float
  
  @staticmethod
  def map_point_values[T](dict_with_points: dict[T, _PointDict]) -> dict[T, Point]:
    """Transform dicts with `PointDict` values to dicts with `Point` values."""
    
    return {
      key: Point(**point)
      for key, point in dict_with_points.items() }
  
  @staticmethod
  def parse_point_keyed_dict[T](point_keyed_dict: dict[DirectionKeys, T]) -> MappingProxyType[ArrowDirections, T]:
    """Transform dicts with keys that are `DirectionKeys` values to immutable dicts with `ArrowDirections` keys."""
    
    return MappingProxyType({
      direction: value
      for key, value in point_keyed_dict.items()
      if (direction := ArrowDirections.from_key(key)) is not None })

  class _GeometryDict(typing.TypedDict):
    arrow_positions: dict[DirectionKeys, ArrowGeometry._PointDict]
    arrow_waypoints: dict[DirectionKeys, list[ArrowGeometry._PointDict]]
    double_arrow_waypoints: dict[DoubleArrowDirections, list[ArrowGeometry._PointDict]]
  
  def read_geometry_file(self, filepath: str):
    """Read geometry .json file and transform into immutable `Point` based dicts."""

    data: ArrowGeometry._GeometryDict = self.read_file(filepath)
    
    self.points = self.parse_point_keyed_dict(
      self.map_point_values(data["arrow_positions"]))

    self.waypoints = self.parse_point_keyed_dict({
      key: tuple(Point(**point) for point in point_list)
      for key, point_list in data["arrow_waypoints"].items() })

    self.double_arrow_waypoints = MappingProxyType({
      direction: tuple(Point(**point) for point in point_list)
      for key, point_list in data["double_arrow_waypoints"].items()
      if (direction := DoubleArrowDirections.from_key(key)) is not None })


class ShapeFactory:
  """Base class for factories that make lists of cell waypoints to facilitate conversion to grid waypoints."""

  STROKE_THICKNESS: float
  
  def __init__(self, cell_position: Point):
    self.cell_position = cell_position
  
  def to_grid_waypoints(self, cell_waypoints: list[Point]) -> list[Point]:
    """Adds an offset to each waypoint.
    Used to transform positions within a cell to positions on the sudoku grid"""

    return [round(waypoint + self.cell_position, 3) for waypoint in cell_waypoints]


class ArrowFactory(ShapeFactory):
  """Makes basic arrows that are a series of SVG path points defining the shape of the arrow.
  Can be standalone as basic arrows or function as the tip of angled arrows."""

  STROKE_THICKNESS = 0.0265625

  def __init__(self, cell_position: Point):
    super().__init__(cell_position)

  def make_arrow(self, position: ArrowDirections, direction: ArrowDirections) -> list[Point]:
    """Make a basic arrow consisting of a list of grid-referenced waypoints.
    Arrow waypoints are stored with the arrow pointing away from the centre of the cell.
    For an arrow not pointing away from the centre of the cell, we need to get the arrow pointing
    in the correct direction and offset it to the correct position."""

    if position == direction:
      return self.to_grid_waypoints(arrow_geometry.waypoints[direction])
    offset = arrow_geometry.points[position] - arrow_geometry.points[direction]
    return self.to_grid_waypoints([waypoint + offset for waypoint in arrow_geometry.waypoints[direction]])


class LineFactory(ShapeFactory):
  """Makes lines for angled arrows, each consisting of a series of SVG path points.
  Lines are designed to use stroke rather than fill to draw the body of an angled arrow to avoid needing to handle curves."""

  STROKE_THICKNESS = ArrowFactory.STROKE_THICKNESS + 0.05

  def __init__(self, cell_position: Point):
    super().__init__(cell_position)
  
  def find_closest_side_point(self, line_point: Point, direction: Point) -> Point:
    """Get the closest side point to the point along direction.
    Only works if direction has a component equal to zero, otherwise will effectively project sidepoint from the centre."""

    return Point(
      round(line_point.x) if direction.x != 0 else line_point.x,
      round(line_point.y) if direction.y != 0 else line_point.y)
  
  def make_line(self, positions: list[ArrowDirections]) -> list[Point]:
    # TODO: Rewrite this method to not use vector flipping and make the direction vectors a lot more clear
    #       Investigate proper vector rotation, dot product, matrices for line representation
    #       It should be rotating the vector from bend point to tip point by 90 degrees in the direction of the
    #       closest cell wall and offsetting the bend point by the distance to the cell wall along that rotated vector
    """Makes a line from three points. The points define a right angle from the centre of the side of the cell to the centre of the arrow tip.
    Applies an offset to the point on the cell wall to counteract the locus of radius `STROKE_THICKNESS / 2` around the point."""

    points = [arrow_geometry.points[position] for position in positions]

    side_point = self.find_closest_side_point(points[0], (
      (positions[2].get_point() - positions[1].get_point()).normalise().perpendicular()
      if positions[0] == positions[1]
      else (points[0] - points[1]).normalise()))
    
    offset_side_point = side_point - (side_point - points[1]).normalise() * (self.STROKE_THICKNESS / 2)
    return self.to_grid_waypoints([offset_side_point, *points[1:]])


class ArrowBuilderBase:
  def __init__(self):
    self.arrows: list[list[Point]] = []
    self.lines: list[list[Point]] = []


class CellArrowBuilder(ArrowBuilderBase):
  """Parses arrow specification strings into a list of specification tuples."""

  def __init__(self, cell_position: Point, specification_string: str):
    super().__init__()
    self.arrow_factory = ArrowFactory(cell_position)
    self.line_factory = LineFactory(cell_position)
    self.injest_specification_string(specification_string)

  def make_arrow_tip(self, line_directions: list[ArrowDirections]) -> list[Point]:
    """Calculates the position and direction of the arrow tip based
    on the `ArrowDirections` describing the given line"""

    tip_position = line_directions[-1]
    tip_direction = ArrowDirections.from_point(
      tip_position.get_point() - line_directions[-2].get_point())
    return self.arrow_factory.make_arrow(tip_position, tip_direction)
  
  def expand_shorthand(self, specification_string: str) -> str:
    """Expands shorthand variants of specification string tokens:
      Basic arrows: "w" -> "w:w", "wd:axq" -> "w:wd:ax:xq:q"
      Angled arrows: "{wd}" -> "{wwd}" """
    
    def expand_small(string: str) -> str:
      """Pattern: any char not preceded/followed by colon or within braces gets duplicated around a colon"""

      return re.sub(r'(?<!:)(\w)(?!:|\w*\})', r'\1:\1', string)

    def expand_bent(string: str) -> str:
      """Pattern: the first of two chars within braces gets duplicated"""

      return re.sub(r'(?<=\{)(\w)(?=\w\})', r'\1\1', string)

    return expand_small(expand_bent(specification_string))

  def injest_specification_string(self, specification_string: str):
    """Extracts specification tokens from specification_string and transforms
    them into a list of arrow specifications line specifications."""
    
    for token_match in re.finditer(
        r'(?P<basic>\w:\w)|(?:\{(?P<angled>\w+)\})',
        self.expand_shorthand(specification_string)):
      group_dict = {
        name: value
        for name, value in token_match.groupdict().items()
        if value is not None }
      
      match group_dict:
        case { 'basic': specification }:
          position, direction = ArrowDirections.from_keys(specification.split(':'))
          self.arrows.append(self.arrow_factory.make_arrow(position, direction))
        case { 'angled': specification }:
          directions = ArrowDirections.from_keys(specification)
          self.lines.append(self.line_factory.make_line(directions))
          self.arrows.append(self.make_arrow_tip(directions))


class DoubleArrowBuilder(ArrowBuilderBase):
  """Parses arrow specification strings into a list of specification tuples."""

  def __init__(self, lines: list[str]):
    super().__init__()
    self.injest_double_arrow_grid(lines)
  
  def make_arrow(self, position: Point, direction: DoubleArrowDirections) -> list[Point]:
    """Make a double arrow consisting of a list of grid-referenced waypoints, positioned at the specified coordinate."""

    return [round(waypoint + position, 3) for waypoint in arrow_geometry.double_arrow_waypoints[direction]]

  def injest_double_arrow_grid(self, lines: list[str]):
    """Extracts double arrows identifiers from double arrow grid and transforms
    them into a list of arrow specifications."""

    self.arrows = [
      self.make_arrow(Point(position_index / 4, line_index / 2), direction)
      for line_index, line in enumerate(lines)
      for position_index, character in enumerate(line)
      if (direction := DoubleArrowDirections.from_key(character)) is not None]


class ArrowJSONWriter:
  """Creates JSON output files containing SVG path coordinates"""

  BASE_PATH = "output"
  
  @staticmethod
  def collapse_xy_objects(json: str) -> str:
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
  
  @classmethod
  def write_file(cls, filename: str, colour: str, shapes: list[list[Point]], thickness: float):
    """Creates a JSON file containing SVG path coordinates"""

    filepath = f"{cls.BASE_PATH}/{colour}/{filename}.json"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as output_file:
      output_file.writelines(
        cls.collapse_xy_objects(json.dumps({
          "lines": [[asdict(point) for point in row] for row in shapes],
          "style": { "thickness": thickness, "color": colour }
        }, indent=2)))


class ArrowMaker(JSONFileInjester):
  """Generates arrow path data for Sudoku Maker from input.json specifications.
  Handles:
    - basic arrows;
    - angled arrows consisting of a line and an arrow tip; and
    - double arrows."""
  
  def __init__(self, colour: str, cell_specifications: list[ArrowBuilderBase]):
    self.colour = colour

    def flatten(list_):
      return [item for sublist in list_ for item in sublist]

    self.arrows = flatten([
      cell_specification.arrows
      for cell_specification in cell_specifications])
    
    self.lines = (lines if any(
      (lines := flatten([
        cell_specification.lines
        for cell_specification in cell_specifications]))
    ) else None)

  class _SpecificationDict(typing.TypedDict):
    colour: str
    grid: list[list[str]] | None
    doubles_grid: list[str] | None

  @classmethod
  def get_arrow_builders(cls, specification: ArrowMaker._SpecificationDict) -> list[ArrowBuilderBase]:
    """Convert a specification object to a collection of ArrowBuilders"""

    arrow_builders = []

    if "grid" in specification:
      for row_index, row in enumerate(specification["grid"]):
        for column_index, specification_string in enumerate(row):
          if specification_string != "":
            arrow_builders.append(CellArrowBuilder(Point(column_index, row_index), specification_string))
    
    if "doubles_grid" in specification:
      arrow_builders.append(DoubleArrowBuilder(specification["doubles_grid"]))
    
    return arrow_builders

  @classmethod
  def from_specification_file(cls, filepath: str) -> list[ArrowMaker]:
    """Read specifications .json file and use it to create a list of `ArrowBuilders`."""

    input_data: list[ArrowMaker._SpecificationDict] = cls.read_file(filepath)

    return [
      ArrowMaker(specification["colour"], cls.get_arrow_builders(specification))
      for specification in input_data]
  
  def write_lines_file(self, filename: str):
    ArrowJSONWriter.write_file(filename, self.colour, self.lines, LineFactory.STROKE_THICKNESS)
  
  def write_arrows_file(self, filename: str):
    ArrowJSONWriter.write_file(filename, self.colour, self.arrows, ArrowFactory.STROKE_THICKNESS)


def main():
  # Initialise module level immutable geometry reference
  global arrow_geometry
  arrow_geometry = ArrowGeometry("data/arrow_geometry.json")
  
  for arrow_builder in ArrowMaker.from_specification_file("input.json"):
    if (has_lines := arrow_builder.lines is not None):
      arrow_builder.write_lines_file("1-lines")
    
    arrow_builder.write_arrows_file("2-arrows" if has_lines else "arrows")

if __name__ == "__main__":
  main()

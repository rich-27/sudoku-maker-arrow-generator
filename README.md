# Arrow Generator

A tool to create arrows for [Sudoku Maker](https://sudokumaker.app/), using its Cosmetic Line Tool feature, for use on [SudokuPad](https://sudokupad.app/).

Sudoku Maker's puzzle element data is edited directly to create the necessary shapes, with some properties replaced in the generated JSON during the sharing to SudokuPad process.

Enable advanced tools on Sudoku Maker via:
```
Preferences -> Advanced -> Enable advanced tools
```

## Usage Instructions

The tool currently supports two types of arrows. Instructions are given in the following sections for the creation of each arrow type.

### Small Arrows

1. Edit `arrow-generator/input.json`:
    - It must be a list of specification objects of the following form:
      ```py
      {
        "type": Literal["small" | "bent"],
        "colour": r'#[0-9]{9}',
        "grid": list[list[ArrowString]]
      }
      ```
    - Each `ArrowString` in grid represents a cell and must be of the form `''.join(list[ArrowSpecifier])`
      - `ArrowSpecifier` is either a single `DirectionLetter` or `f"{DirectionLetter}:{DirectionLetter}"`
      - `DirectionLetter = Literal['w', 'e' 'd', 'c', 'x', 'z', 'a', 'q']`.
    - Each `DirectionLetter` corresponds to its associated direction, as indicated in the following diagram:
      ```
      +-------+
      | q w e |
      | a   d |
      | z x c |
      +-------+
      ```
    - Arrows can be represented by a single letter or by `{letter}:{letter}` to give the position within the cell and direction separately.
2. Run `arrow-generator/arrows.py`.
3. This tool generates JSON data for each specification in `input.json`. For each JSON file:
    - On Sudoku Maker, create a new `Cosmetic lines` element and replace the JSON in `Edit data as JSON` with the contents of `arrow-generator/output/small/{arrow colour}.json`
4. When using the `Share` menu to open the puzzle in SudokuPad, use `Edit JSON` to apply the following changes:
    - Add a `"fill": {arrow colour}` property to each line object generated with this tool.
    - This can be achieved using find and replace:
      - Find: `"color": "#999f",`
      - Replace: `"color": "#999f","fill": "#999f",`

### Bent Arrows

1. Edit `arrow-generator/input.json`:
    - Add a specification object with `"type": "bent"`.
    - The remaining fields (`colour`, `grid`) follow the same structure described in [Small Arrows](#small-arrows).
    > [!NOTE]
    > The arrow generator only supports bent arrows formed from the following pairs of directions:
    >```
    >e:w, e:d, c:d, c:x, z:x, z:a, q:a, q:w
    >```
    > Using any other direction pairs will cause the generator to fail.
2. Run `arrow-generator/arrows.py`.
3. The tool will generate pairs of JSON files:
    - `arrow-generator/output/bent/{arrow colour}/1-lines.json`
    - `arrow-generator/output/bent/{arrow colour}/2-arrows.json`
  
   For each file:
    - On Sudoku Maker, create a new `Cosmetic lines` element and replace the JSON in `Edit data as JSON` with the contents of the generated file.
4. When using the `Share` menu to open the puzzle in SudokuPad, use **Edit JSON** to apply the following changes:
    - Add a `"fill": {arrow colour}` property to each line object generated with this tool.
      - Find: `"color": "#999f",(\n\s*)"thickness": 1.7`
      - Replace: `"color": "#999f",\1"fill": "#999f",\1"thickness": 1.7`
    - Add a `"stroke-linecap": "square"` property to each arrow object:
      - Find: `"color": "#999f",(\n\s*)"thickness": 4.9`
      - Replace: `"color": "#999f",\1"thickness": 4.9,\1"stroke-linecap": "square"`

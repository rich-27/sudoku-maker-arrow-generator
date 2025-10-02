# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Planned

- Extend bent arrow syntax to incorporate:
  - `{qwxc}` for a double bend
  - `{<qad}` for double headed arrows
  - `{wsd}` for arrows that bend in the centre of the cell
  - `{xde}` for a 45° bend
    - How does this interact with cell walls?
    - Would likely need a special tip for diagonal wall connections (both corner and side)

[//]: # ([2.0.0] - 2025-10-??)

## [Unreleased]

### Changed

- New bent arrow syntax:
  - `z:x` is now `{az}`, which is shorthand for `{aaz}`
  - The new format specifies `{{tail position}, {bend position}, {tip position}}`
  - This allows for new big bent arrows such as `{qec}`
  - After some use this feels a lot more intuitive
  - By default these arrows:
    - start from the adjacent cell wall
    - end in a tip

### Removed

- No type parameter needed in JSON specifications
  - Small arrows and bent arrows having distinct syntax means type can be inferred

## [1.0.0] - 2025-10-02

Initial release

[unreleased]: https://github.com/rich-27/sudoku-maker-arrow-generator/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/rich-27/sudoku-maker-arrow-generator/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/rich-27/sudoku-maker-arrow-generator/releases/tag/v1.0.0
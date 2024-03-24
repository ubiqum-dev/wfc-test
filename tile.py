from enum import StrEnum
from functools import reduce
from random import choice, choices
from typing import Self, Iterator, Literal

import pygame
from pygame.sprite import Sprite


class Surface(StrEnum):
    GRASS: str = "G"
    WATER: str = "W"
    FOREST: str = "F"
    SWAMP: str = "S"
    SAND: str = "s"


connections = {
    Surface.GRASS: {Surface.GRASS, Surface.FOREST, Surface.SAND, Surface.WATER},
    Surface.FOREST: {Surface.FOREST, Surface.GRASS, Surface.SWAMP},
    Surface.SWAMP: {Surface.SWAMP, Surface.FOREST},
    Surface.WATER: {Surface.WATER, Surface.SAND, Surface.GRASS},
    Surface.SAND: {Surface.SAND, Surface.WATER, Surface.GRASS},
}

colors_day = {
    Surface.GRASS: (0, 255, 0),
    Surface.FOREST: (1, 50, 32),
    Surface.SWAMP: (81, 55, 67),
    Surface.WATER: (20, 20, 255),
    Surface.SAND: (194, 178, 128),
}
colors_night = {
    Surface.GRASS: (0, 150, 0),
    Surface.FOREST: (1, 0, 12),
    Surface.SWAMP: (31, 5, 17),
    Surface.WATER: (0, 0, 205),
    Surface.SAND: (134, 128, 78),
}


WEIGHTS = {
    Surface.GRASS: 70,
    Surface.FOREST: 12,
    Surface.SWAMP: 10,
    Surface.WATER: 20,
    Surface.SAND: 22,
}


class Tile(Sprite):
    def __init__(self, x: int, y: int, value: Surface | None = None, color_schema: Literal["day", "night"] = "day"):
        super().__init__()
        if color_schema == "day":
            self.colors = colors_day
        else:
            self.colors = colors_night
        self.x: int = x
        self.y: int = y
        self.size: int = 5
        self.value: Surface = value or Surface.FOREST
        self.possible_values: set[Surface] = {value} if value else set(Surface)
        self.image = pygame.Surface((self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x * self.size, self.y * self.size)

    @property
    def entropy(self) -> int:
        return len(self.possible_values)

    def update_values(self, _values: set[Surface]) -> bool:
        """Update possible surfaces and return if they were changed"""
        if _values - self.possible_values:
            return False

        if self.possible_values == _values:
            return False

        self.possible_values = _values

        if len(self.possible_values) == 1:  # no more choices == collapsed
            self.collapse()

        return True

    def collapse(self, value: Surface | None = None) -> Self:
        if value and value in self.possible_values:
            self.value = value
        else:
            list_possible_values = list(self.possible_values)
            weights: list[int] = [WEIGHTS[v] for v in list_possible_values]
            self.value = choices(list_possible_values, weights=weights)[0]

        self.possible_values = {self.value}
        self.image.fill(self.colors[self.value])
        return self

    def possible_neighbor_values(self) -> set[Surface]:
        all_values: list[set[Surface]] = []
        for value in self.possible_values:
            all_values.append(connections[value])
        return reduce(lambda s1, s2: s1 | s2, all_values)

    def __str__(self) -> str:
        if self.entropy > 1:
            return f"{self.entropy}"
        return f"{str(self.value)}"

    def __repr__(self) -> str:
        if self.entropy > 1:
            return f"{self.entropy}"
        return f"{str(self.value)}"


class Chunk:
    def __init__(self, chunk_size: int = 10):
        self.chunk_size: int = chunk_size
        self.IS_DAY: bool = choice([True, False])
        color_schema: Literal["day", "night"] = "day" if self.IS_DAY else "night"
        self.tiles: tuple[tuple[Tile, ...], ...] = tuple(tuple(Tile(x=row, y=col, color_schema=color_schema) for col in range(chunk_size)) for row in range(chunk_size))

    def tile_iter(self, collapsed: bool = False) -> Iterator[Tile]:
        for row in self.tiles:
            for tile in row:
                if collapsed:
                    yield tile

                if tile.entropy == 1:
                    continue
                yield tile

    def is_ready(self) -> bool:
        for tile in self.tile_iter():
            if tile.entropy > 1:
                return False
        return True

    def get_tile_neighbors(self, tile: Tile) -> list[Tile]:
        neighbors: list[Tile] = []
        if tile.x > 0:
            neighbors.append(self.tiles[tile.x - 1][tile.y])  # left
        if tile.x < self.chunk_size - 1:
            neighbors.append(self.tiles[tile.x + 1][tile.y])  # right
        if tile.y > 0:
            neighbors.append(self.tiles[tile.x][tile.y - 1])  # top
        if tile.y < self.chunk_size - 1:
            neighbors.append(self.tiles[tile.x][tile.y + 1])  # bottom

        return neighbors

    @staticmethod
    def calculate_values(tiles: list[Tile]) -> set[Surface]:
        all_neighbor_surfaces: list[set[Surface]] = []
        for tile in tiles:
            all_neighbor_surfaces.append(tile.possible_neighbor_values())

        return reduce(lambda s1, s2: s1 & s2, all_neighbor_surfaces)

    def propagate(self, tile: Tile) -> bool:
        """Propagate cell values and return if values were changed"""
        neighbors: list[Tile] = self.get_tile_neighbors(tile)
        possible_values: set[Surface] = self.calculate_values(neighbors)
        return tile.update_values(possible_values)

    def find_lowest_entropy(self) -> Tile:

        low_entropy_tiles: list[Tile] = []
        min_entropy: int = 9999
        for tile in self.tile_iter():
            if tile.entropy < min_entropy:
                min_entropy = tile.entropy
                low_entropy_tiles = [tile]
            elif tile.entropy == min_entropy:
                low_entropy_tiles.append(tile)

        return choice(low_entropy_tiles)

    def print(self) -> None:
        for row in self.tiles:
            print(row)
        print("_" * 30)

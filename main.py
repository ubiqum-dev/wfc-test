import pygame

from tile import Tile, Chunk


def propagate(chunk: Chunk, tile: Tile) -> None:
    initial_neighbors: list[Tile] = chunk.get_tile_neighbors(tile)
    propagation_results: list[bool] = []
    for neighbor in initial_neighbors:
        propagation_results.append(chunk.propagate(neighbor))

    if any(propagation_results):
        for neighbor in initial_neighbors:
            propagate(chunk, neighbor)


def generation_step(chunk: Chunk) -> None:
    initial_tile: Tile = chunk.find_lowest_entropy()
    initial_tile.collapse()
    propagate(chunk, initial_tile)


def generate(chunk_size: int = 10) -> Chunk:
    chunk: Chunk = Chunk(chunk_size)

    while not chunk.is_ready():
        generation_step(chunk)
    return chunk


def main() -> None:
    pygame.init()
    chunk_size: int = 50
    WIDTH: int = chunk_size * 5
    HEIGHT: int = chunk_size * 5
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chunk generator")
    clock = pygame.time.Clock()

    # chunk.tiles[10][10].collapse(Surface.SWAMP)
    # propagate(chunk, chunk.tiles[10][10])
    # chunk.tiles[50][50].collapse(Surface.WATER)
    # propagate(chunk, chunk.tiles[50][50])

    running = True
    first_run: bool = True
    while running:
        all_sprites = pygame.sprite.Group()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if first_run or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                chunk: Chunk = Chunk(chunk_size)
                first_run = False

        for tile in chunk.tile_iter(collapsed=True):
            all_sprites.add(tile)

        if not chunk.is_ready():
            generation_step(chunk)
            all_sprites.draw(screen)
            pygame.display.flip()


if __name__ == '__main__':
    main()

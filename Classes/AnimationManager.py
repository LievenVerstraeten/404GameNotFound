import pygame


class AnimationManager:
    def __init__(self, image_path, num_frames):
        # Load the sprite sheet using pygame
        self.sprite_sheet = pygame.image.load(image_path).convert_alpha()

        self.num_frames = num_frames
        self.frames = []

        # Calculate width and height of a single frame
        sheet_width = self.sprite_sheet.get_width()
        sheet_height = self.sprite_sheet.get_height()
        frame_width = sheet_width // num_frames
        frame_height = sheet_height

        # Extract frames
        for i in range(num_frames):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(self.sprite_sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
            self.frames.append(frame)

        self.current_frame = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.1  # 100ms per frame

    def update(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.current_frame = (self.current_frame + 1) % self.num_frames

    def get_current_image(self):
        return self.frames[self.current_frame]

import pygame


class CollisionSystem:

    @staticmethod
    def bullet_vs_enemy(bullet, enemy):

        if bullet is None or enemy is None:
            return False

        if not bullet.is_active:
            return False

        if bullet.has_hit:
            return False

        if hasattr(enemy, "is_alive"):
            if not enemy.is_alive:
                return False

        if hasattr(bullet, "get_swept_rect"):
            bullet_rect = bullet.get_swept_rect()
        elif hasattr(bullet, "get_rect"):
            bullet_rect = bullet.get_rect()
        else:
            return False

        if hasattr(enemy, "get_hitbox"):
            enemy_rect = enemy.get_hitbox()
        elif hasattr(enemy, "get_rect"):
            enemy_rect = enemy.get_rect()
        elif hasattr(enemy, "rect"):
            enemy_rect = enemy.rect
        else:
            return False

        if not bullet_rect.colliderect(enemy_rect):
            return False

        bullet.impact()

        return True

    @staticmethod
    def bullets_vs_enemies(bullets, enemies):

        collisions = []

        if not bullets or not enemies:
            return collisions

        for bullet in bullets:

            if bullet is None:
                continue

            if not bullet.is_active:
                continue

            if bullet.has_hit:
                continue

            for enemy in enemies:

                if enemy is None:
                    continue

                if not bullet.is_active:
                    break

                if hasattr(enemy, "is_alive"):
                    if not enemy.is_alive:
                        continue

                if CollisionSystem.bullet_vs_enemy(
                    bullet,
                    enemy
                ):
                    collisions.append(
                        (bullet, enemy)
                    )

        return collisions

    @staticmethod
    def player_vs_enemy(player, enemy):

        if player is None or enemy is None:
            return False

        if hasattr(player, "get_hitbox"):
            player_rect = player.get_hitbox()
        elif hasattr(player, "get_rect"):
            player_rect = player.get_rect()
        elif hasattr(player, "rect"):
            player_rect = player.rect
        else:
            return False

        if hasattr(enemy, "get_hitbox"):
            enemy_rect = enemy.get_hitbox()
        elif hasattr(enemy, "get_rect"):
            enemy_rect = enemy.get_rect()
        elif hasattr(enemy, "rect"):
            enemy_rect = enemy.rect
        else:
            return False

        return player_rect.colliderect(enemy_rect)
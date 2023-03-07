from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    '''Пользовательская моедль юзера'''
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLES = (
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Админ'),
    )

    email = models.EmailField(unique=True, verbose_name='Электронный адрес')
    role = models.CharField(
        max_length=50, choices=ROLES, default=USER,
        verbose_name='Права доступа'
    )
    bio = models.TextField(blank=True, null=True, verbose_name='О Себе')

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = (
            models.CheckConstraint(
                name='not_equal_username_me',
                check=~models.Q(username='me'),
            ),
        )

    @property
    def is_user(self):
        '''Свойство для реализации прав доступа для обычного пользователя'''
        return self.role == self.USER

    @property
    def is_moderator(self):
        '''Свойство для реализации прав доступа для модератора'''
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        '''Свойство для реализации прав доступа
        для администратора или модератора'''
        return self.role == self.ADMIN or self.is_superuser

import re

from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from api.fields import CurrentReview, CurrentTitle
from users.models import User
from reviews.models import Category, Comment, Genre, Review, Title


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(max_length=254, required=True)

    class Meta:
        fields = ('username', 'email',)

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError(
                'Нельзя использовать "me" в качестве имени.'
            )
        if not re.match(r'^[\w.@+-]+\Z', username):
            raise serializers.ValidationError(
                'Имя должно состоять из букв латинского алфавита'
                'цифр и допустимых символов "@/./+/-/_"'
            )
        return username


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        fields = ('username', 'confirmation_code', )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio',
                  'role', )
        lookup_field = 'username'

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError(
                'Нельзя использовать "me" в качестве имени.'
            )
        return username


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'slug',)
        lookup_field = 'slug'


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ('name', 'slug',)
        lookup_field = 'slug'


class TitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        slug_field='slug', many=True, queryset=Genre.objects.all()
    )
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category',)


class ReadOnlyTitleSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(read_only=True)
    genre = GenreSerializer(many=True)
    category = CategorySerializer()

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category',
        )


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели отызвы"""
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True,
        default=serializers.CurrentUserDefault()
    )
    score = serializers.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ]
    )
    title = serializers.HiddenField(default=CurrentTitle())

    class Meta:
        model = Review
        fields = ('id', 'title', 'text', 'author', 'score', 'pub_date', )
        validators = (
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=('title', 'author', ),
                message='Review has already been posted by this author.'
            ),
        )


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для модели комментарии"""
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True,
        default=serializers.CurrentUserDefault()
    )

    review = serializers.HiddenField(default=CurrentReview())

    class Meta:
        model = Comment
        fields = ('id', 'review', 'text', 'author', 'pub_date', )

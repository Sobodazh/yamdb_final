from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Genre, Review, Title
from users.models import User

from .filters import TitleFilter
from .permissions import (IsAdmin, IsAdminOrModeratorIsAuthorOrReadOnly,
                          IsAdminOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, ReadOnlyTitleSerializer,
                          ReviewSerializer, SignupSerializer, TitleSerializer,
                          TokenSerializer, UserSerializer)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.data.get('username')
    email = serializer.data.get('email')

    try:
        user, _ = User.objects.get_or_create(username=username, email=email)
    except IntegrityError as err:
        return Response(
            f'Возникли проблемы: {err}', status=status.HTTP_400_BAD_REQUEST
        )
    else:
        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            'Приветствую, это приложение YamDB',
            f'Ваш код подтверждения: "{confirmation_code}"',
            'YA@yamdb.ru',
            (user.email, ),
            fail_silently=False,
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_jwt_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.data.get('username')
    user = get_object_or_404(User, username=username)
    confirmation_code = serializer.data.get('confirmation_code')

    if default_token_generator.check_token(user, confirmation_code):
        token = RefreshToken.for_user(user).access_token
        return Response(f'Ваш токен: {token}', status=status.HTTP_200_OK)
    return Response(
        {'Введите верный код подтверждения или попробуйте позднее'},
        status=status.HTTP_400_BAD_REQUEST
    )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdmin, )

    filter_backends = (SearchFilter, )
    search_fields = ('username', )
    http_method_names = ['get', 'post', 'patch', 'delete']

    lookup_field = 'username'

    @action(detail=False, methods=('GET', 'PATCH', ),
            permission_classes=(IsAuthenticated, ))
    def me(self, request):
        user = get_object_or_404(User, id=request.user.id)

        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save(role=user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly, )
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (SearchFilter, )
    search_fields = ('name', )
    lookup_field = 'slug'


class GenreViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly, IsAuthenticatedOrReadOnly, )
    filter_backends = (SearchFilter, )
    search_fields = ('name', )
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(
        rating=Avg('reviews__score')
    ).order_by('name')
    permission_classes = (IsAdminOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadOnlyTitleSerializer
        return TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAdminOrModeratorIsAuthorOrReadOnly, )

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        return title.reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAdminOrModeratorIsAuthorOrReadOnly, )

    def get_queryset(self):
        review = get_object_or_404(
            Review, title_id=self.kwargs.get('title_id'),
            id=self.kwargs.get('review_id')
        )
        return review.comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

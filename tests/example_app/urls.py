from django.contrib.auth.models import User
from django.urls import re_path
from rest_framework import serializers

from strawberry.django.views import GraphQLView,AsyncGraphQLView

from tests.example_app.schema import schema, sync_schema


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "is_staff"]

urlpatterns = [
    re_path(r"^graphql/?$", AsyncGraphQLView.as_view(schema=schema), name="graphql"),
    re_path(
        r"^sync-graphql/?$", GraphQLView.as_view(schema=sync_schema),
        name="sync_graphql",
    ),
]

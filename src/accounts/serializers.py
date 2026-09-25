from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "role",
            "tenant",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tenant",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        requester = request.user

        tenant = attrs.get("tenant")
        role = attrs.get("role")

        if requester.role == "TENANT_ADMIN":
            # Tenant Admin cannot manage another tenant.
            if tenant and tenant.id != requester.tenant_id:
                raise serializers.ValidationError(
                    "You cannot manage users outside your tenant."
                )

            # Tenant Admin can only manage Tenant Users.
            if role is not None and role != "TENANT_USER":
                raise serializers.ValidationError(
                    "Tenant Admins can only manage Tenant Users."
                )

            # Prevent changing an existing Tenant User into another role
            # when the role is omitted from a partial update.
            if self.instance and self.instance.role != "TENANT_USER":
                raise serializers.ValidationError(
                    "Tenant Admins can only manage Tenant Users."
                )

        return attrs
    def create(self, validated_data):
        password = validated_data.pop("password", None)

        if not password:
            raise serializers.ValidationError(
                {"password": "Password is required when creating a user."}
            )

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance
from rest_framework import serializers
from .models import User, UserRole


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
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        requester = request.user

        tenant = attrs.get("tenant")
        role = attrs.get("role")

        if requester.role == UserRole.TENANT_ADMIN:
            if tenant and tenant.id != requester.tenant_id:
                raise serializers.ValidationError(
                    "You cannot manage users outside your tenant."
                )

            if role is not None and role != UserRole.TENANT_USER:
                raise serializers.ValidationError(
                    "Tenant Admins can only manage Tenant Users."
                )

            if self.instance and self.instance.role != UserRole.TENANT_USER:
                raise serializers.ValidationError(
                    "Tenant Admins can only manage Tenant Users."
                )

        if requester.role == UserRole.ADMIN:
            platform_roles = [
                UserRole.SUPER_ADMIN,
                UserRole.ADMIN,
                UserRole.SUPER_VIEWER,
            ]
            if role in platform_roles:
                raise serializers.ValidationError(
                    "Admins cannot assign platform-privileged roles."
                )

        if (
            role in [UserRole.TENANT_USER, UserRole.TENANT_ADMIN]
            and requester.role != UserRole.TENANT_ADMIN
            and not tenant
        ):
            raise serializers.ValidationError(
                "Tenant users and admins must belong to a tenant."
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
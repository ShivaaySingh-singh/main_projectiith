from rest_framework import serializers
from .models import Expenditure, Commitment, SeedGrant, TDGGrant

# ✅ Base Serializer with Grant Support
class GrantRelatedSerializer(serializers.ModelSerializer):
    """Base serializer for models with seed_grant/tdg_grant FK"""
    grant_no_display = serializers.SerializerMethodField()
    seed_grant_short = serializers.CharField(source='seed_grant.short_no', read_only=True, allow_null=True)
    tdg_grant_short = serializers.CharField(source='tdg_grant.short_no', read_only=True, allow_null=True)
    
    def get_grant_no_display(self, obj):
        """Return full grant number for display"""
        if obj.seed_grant:
            return obj.seed_grant.grant_no
        elif obj.tdg_grant:
            return obj.tdg_grant.grant_no
        return ''
    
    def validate(self, data):
        """Ensure either seed_grant or tdg_grant is provided (not both)"""
        seed_grant = data.get('seed_grant')
        tdg_grant = data.get('tdg_grant')
        
        # For updates, check existing values
        if self.instance:
            seed_grant = seed_grant if 'seed_grant' in data else self.instance.seed_grant
            tdg_grant = tdg_grant if 'tdg_grant' in data else self.instance.tdg_grant
        
        if not seed_grant and not tdg_grant:
            raise serializers.ValidationError("Either seed_grant or tdg_grant must be provided")
        
        if seed_grant and tdg_grant:
            raise serializers.ValidationError("Cannot have both seed_grant and tdg_grant")
        
        return data
    
    def update(self, instance, validated_data):
        """Handle grant updates properly"""
        if 'seed_grant' in validated_data and validated_data['seed_grant']:
            instance.tdg_grant = None
        if 'tdg_grant' in validated_data and validated_data['tdg_grant']:
            instance.seed_grant = None
        
        return super().update(instance, validated_data)


# ✅ Expenditure Serializer
class ExpenditureSerializer(GrantRelatedSerializer):
    class Meta:
        model = Expenditure
        fields = [
            'id', 'date', 'head', 'particulars', 'amount', 'remarks',
            'seed_grant', 'tdg_grant',
            'grant_no_display', 'seed_grant_short', 'tdg_grant_short'
        ]
        extra_kwargs = {
            'seed_grant': {'required': False, 'allow_null': True},
            'tdg_grant': {'required': False, 'allow_null': True},
        }


# ✅ Commitment Serializer
class CommitmentSerializer(GrantRelatedSerializer):
    class Meta:
        model = Commitment
        fields = [
            'id', 'date', 'head', 'particulars', 'gross_amount', 'remarks',
            'seed_grant', 'tdg_grant',
            'grant_no_display', 'seed_grant_short', 'tdg_grant_short'
        ]
        extra_kwargs = {
            'seed_grant': {'required': False, 'allow_null': True},
            'tdg_grant': {'required': False, 'allow_null': True},
        }


# ✅ SeedGrant Serializer (Simple - no FK relations)
class SeedGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedGrant
        fields = '__all__'


# ✅ TDGGrant Serializer (Simple - no FK relations)
class TDGGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = TDGGrant
        fields = '__all__'
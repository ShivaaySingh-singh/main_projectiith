from rest_framework import serializers
from .models import Expenditure, Commitment, SeedGrant, TDGGrant, FundRequest, Project,BillInward,Faculty, Payment, Receipt, TDSSection,TDSRate

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
        return ""
    
    def validate(self, data):
        seed = self.initial_data.get('seed_grant')
        tdg = self.initial_data.get('tdg_grant')

        if not seed and not tdg:
            raise serializers.ValidationError(
                "Either seed_grant or tdg_grant is required"
            )
        
        if seed and tdg:
            raise serializers.ValidationError(
                "Select only one grant type (Seed or TDG)"

            )
        return data 




       
    
    def create(self, validated_data):
    
        if validated_data.get('seed_grant'):
            validated_data['tdg_grant'] = None

        if validated_data.get('tdg_grant'):
            validated_data['seed_grant'] = None

        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle grant updates properly"""
        if 'seed_grant' in validated_data and validated_data['seed_grant']:
            instance.tdg_grant = None
        if 'tdg_grant' in validated_data and validated_data['tdg_grant']:
            instance.seed_grant = None
        
        return super().update(instance, validated_data)


# ✅ Expenditure Serializer
class ExpenditureSerializer(GrantRelatedSerializer):
    seed_grant = serializers.SlugRelatedField(slug_field='short_no', queryset=SeedGrant.objects.all(), allow_null=True, required=False)

    tdg_grant = serializers.SlugRelatedField(slug_field='short_no', queryset=TDGGrant.objects.all(), allow_null=True, required=False)
    
    class Meta:
        model = Expenditure
        fields = [
            'id', 'date', 'head', 'particulars', 'amount', 'remarks',
            'seed_grant', 'tdg_grant',
            'grant_no_display', 'seed_grant_short', 'tdg_grant_short'
        ]
        


# ✅ Commitment Serializer
class CommitmentSerializer(GrantRelatedSerializer):
    seed_grant = serializers.SlugRelatedField(slug_field='short_no', queryset=SeedGrant.objects.all(), allow_null=True, required=False)
    tdg_grant = serializers.SlugRelatedField(slug_field='short_no', queryset=TDGGrant.objects.all(), allow_null=True, required=False )
    class Meta:
        model = Commitment
        fields = [
            'id', 'date', 'head', 'particulars', 'gross_amount', 'remarks',
            'seed_grant', 'tdg_grant',
            'grant_no_display', 'seed_grant_short', 'tdg_grant_short'
        ]
        


# ✅ SeedGrant Serializer (Simple - no FK relations)
class SeedGrantSerializer(serializers.ModelSerializer):
    
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    faculty_department = serializers.CharField(source="faculty.department", read_only=True)

    
    class Meta:
        model = SeedGrant
        fields = '__all__'
        read_only_fields = ['short_no']


# ✅ TDGGrant Serializer (Simple - no FK relations)
class TDGGrantSerializer(serializers.ModelSerializer):
    
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    faculty_department = serializers.CharField(source="faculty.department", read_only=True)
    
    
    class Meta:
        model = TDGGrant
        fields = '__all__'
        read_only_fields = ['short_no']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class FundRequestSerializer(serializers.ModelSerializer):
    faculty_username = serializers.CharField(source='faculty.username', read_only=True)
    project_type = serializers.SerializerMethodField()

    class Meta:
        model = FundRequest
        fields = [
            'id', 
            'faculty', 
            'faculty_username',
            'pi_name', 
            'faculty_id',
            'project', 
            'seed_grant', 
            'tdg_grant',
            'project_type',
            'project_no', 
            'project_title', 
            'short_no',
            'head', 
            'particulars', 
            'amount',
            'status', 
            'remarks_by_src',
            'request_date', 
            'updated_date'
        ]

        read_only_fields = [
            'faculty', 
            'pi_name', 
            'faculty_id',
            'project', 
            'seed_grant', 
            'tdg_grant',
            'project_no', 
            'project_title', 
            'short_no',
            'head', 
            'particulars', 
            'amount',
            'request_date', 
            'updated_date'
        ]

    def get_project_type(self, obj):
            """Determine project type for display"""
            if obj.project:
               return 'Project'
            elif obj.seed_grant:
               return 'Seed Grant'
            elif obj.tdg_grant:
               return 'TDG Grant'
            return 'N/A'

    def validate_status(self, value):
            """Validate status choices"""
            valid_statuses = ['pending', 'approved', 'rejected']
            if value not in valid_statuses:
                raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
            return value
    
class BillInwardSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True) 
    faculty = serializers.SlugRelatedField(slug_field="faculty_id", queryset=Faculty.objects.all())
    tds_section = serializers.PrimaryKeyRelatedField(queryset=TDSSection.objects.all(), allow_null=True, required=False)
    tds_rate = serializers.PrimaryKeyRelatedField(queryset=TDSRate.objects.all(), allow_null=True, required=False)
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    # Optional: Display fields for better UI (read-only)
    faculty_id_display = serializers.CharField(source='faculty.faculty_id',  read_only=True, required=False)
    
    
    assigned_to_name = serializers.SerializerMethodField(read_only=True)
    
    status_display = serializers.CharField(
        source='get_bill_status_display',
        read_only=True
    )
    
    class Meta:
        model = BillInward
        fields = '__all__'
    
    def get_assigned_to_name(self, obj):
        """Show assigned admin member name"""
        if obj.whom_to:
            return obj.whom_to.get_full_name() or obj.whom_to.username
        return None
    
class PaymentSerializer(serializers.ModelSerializer):
    pi_name = serializers.CharField(source="faculty.pi_name", read_only=True)
    tds_section = serializers.IntegerField(source="tds_section.id", read_only=False,allow_null=True)
    tds_rate = serializers.IntegerField(source="tds_rate.id", read_only=False, allow_null=True)

    class Meta:
        model = Payment
        fields = '__all__'            

class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'
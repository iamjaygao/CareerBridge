from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationLog, NotificationBatch
)
from .serializers import (
    NotificationSerializer, NotificationListSerializer, NotificationMarkReadSerializer,
    NotificationPreferenceSerializer, NotificationTemplateSerializer, NotificationLogSerializer,
    NotificationBatchSerializer, NotificationStatsSerializer, NotificationCreateSerializer,
    NotificationFilterSerializer
)

class NotificationListView(generics.ListAPIView):
    """User notification list"""
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Apply filter conditions
        serializer = NotificationFilterSerializer(data=self.request.query_params)
        if serializer.is_valid():
            data = serializer.validated_data
            
            if data.get('notification_type'):
                queryset = queryset.filter(notification_type=data['notification_type'])
            
            if data.get('is_read') is not None:
                queryset = queryset.filter(is_read=data['is_read'])
            
            if data.get('priority'):
                queryset = queryset.filter(priority=data['priority'])
            
            if data.get('date_from'):
                queryset = queryset.filter(created_at__date__gte=data['date_from'])
            
            if data.get('date_to'):
                queryset = queryset.filter(created_at__date__lte=data['date_to'])
            
            limit = data.get('limit', 20)
            return queryset[:limit]
        
        return queryset[:20]

class NotificationDetailView(generics.RetrieveAPIView):
    """Notification details"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Get notification details and mark as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return super().retrieve(request, *args, **kwargs)

class NotificationMarkReadView(generics.GenericAPIView):
    """Mark notifications as read"""
    serializer_class = NotificationMarkReadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            
            # Batch mark as read
            notifications = Notification.objects.filter(
                user=request.user,
                id__in=notification_ids
            )
            
            updated_count = notifications.update(
                is_read=True,
                read_at=timezone.now()
            )
            
            return Response({
                'message': f'{updated_count} notifications marked as read',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationMarkAllReadView(generics.GenericAPIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        updated_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'updated_count': updated_count
        })

class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """User notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get or create user notification preferences"""
        user = self.request.user
        preference, created = NotificationPreference.objects.get_or_create(user=user)
        return preference

class NotificationStatsView(generics.GenericAPIView):
    """Notification statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Basic statistics
        total_notifications = Notification.objects.filter(user=user).count()
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        read_count = total_notifications - unread_count
        
        # Statistics by type
        notifications_by_type = Notification.objects.filter(user=user).values(
            'notification_type'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Statistics by priority
        notifications_by_priority = Notification.objects.filter(user=user).values(
            'priority'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Recent notifications
        recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Convert to dictionary format
        type_stats = {item['notification_type']: item['count'] for item in notifications_by_type}
        priority_stats = {item['priority']: item['count'] for item in notifications_by_priority}
        
        data = {
            'total_notifications': total_notifications,
            'unread_count': unread_count,
            'read_count': read_count,
            'notifications_by_type': type_stats,
            'notifications_by_priority': priority_stats,
            'recent_notifications': NotificationListSerializer(recent_notifications, many=True).data
        }
        
        return Response(data)

class NotificationCreateView(generics.CreateAPIView):
    """Create notification (Admin function)"""
    serializer_class = NotificationCreateSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save()

class NotificationTemplateListView(generics.ListAPIView):
    """Notification template list (Admin function)"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationTemplate.objects.filter(is_active=True)

class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Notification template details (Admin function)"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationTemplate.objects.all()

class NotificationLogListView(generics.ListAPIView):
    """Notification delivery logs (Admin function)"""
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationLog.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by delivery method
        delivery_method = self.request.query_params.get('delivery_method')
        if delivery_method:
            queryset = queryset.filter(delivery_method=delivery_method)
        
        # Filter by status
        delivery_status = self.request.query_params.get('delivery_status')
        if delivery_status:
            queryset = queryset.filter(delivery_status=delivery_status)
        
        # Filter by date
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset

class NotificationBatchListView(generics.ListCreateAPIView):
    """Batch notification task list (Admin function)"""
    serializer_class = NotificationBatchSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationBatch.objects.all()

class NotificationBatchDetailView(generics.RetrieveAPIView):
    """Batch notification task details (Admin function)"""
    serializer_class = NotificationBatchSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = NotificationBatch.objects.all()

class NotificationUnreadCountView(generics.GenericAPIView):
    """Get unread notification count"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        
        return Response({
            'unread_count': unread_count
        })

class NotificationDeleteView(generics.DestroyAPIView):
    """Delete notification"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.delete()
        return Response({'message': 'Notification deleted successfully'})

class NotificationDeleteAllView(generics.GenericAPIView):
    """Delete all notifications"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        deleted_count = Notification.objects.filter(user=user).delete()[0]
        
        return Response({
            'message': f'{deleted_count} notifications deleted successfully',
            'deleted_count': deleted_count
        })

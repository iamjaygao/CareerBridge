"""
Unit Tests for Bus Power Policy

Tests the bus resolution and power state logic.
"""

import pytest
from kernel.policies.bus_power import (
    resolve_bus,
    is_bus_powered,
    get_bus_state,
    get_all_buses,
    BUS_POWER,
)


class TestBusResolution:
    """Test path-to-bus resolution logic"""
    
    def test_kernel_core_bus(self):
        """Kernel paths should resolve to KERNEL_CORE_BUS"""
        assert resolve_bus('/kernel/pulse/summary/') == 'KERNEL_CORE_BUS'
        assert resolve_bus('/superadmin/workload-runtime') == 'KERNEL_CORE_BUS'
    
    def test_ai_bus(self):
        """AI paths should resolve to AI_BUS (consolidated)"""
        assert resolve_bus('/api/v1/ai/') == 'AI_BUS'
        assert resolve_bus('/api/engines/') == 'AI_BUS'
        assert resolve_bus('/api/v1/ats-signals/') == 'AI_BUS'
        assert resolve_bus('/api/v1/chat/') == 'AI_BUS'
        assert resolve_bus('/api/v1/signal-delivery/') == 'AI_BUS'
        assert resolve_bus('/api/v1/decision-slots/') == 'AI_BUS'
    
    def test_mentor_bus(self):
        """Mentor paths should resolve to MENTOR_BUS"""
        assert resolve_bus('/api/v1/mentors/') == 'MENTOR_BUS'
        assert resolve_bus('/api/v1/human-loop/') == 'MENTOR_BUS'
        assert resolve_bus('/api/v1/appointments/') == 'MENTOR_BUS'
        assert resolve_bus('/api/v1/availability/') == 'MENTOR_BUS'
    
    def test_payment_bus(self):
        """Payment paths should resolve to PAYMENT_BUS"""
        assert resolve_bus('/api/v1/payments/') == 'PAYMENT_BUS'
        assert resolve_bus('/api/v1/billing/') == 'PAYMENT_BUS'
    
    def test_search_bus(self):
        """Search paths should resolve to SEARCH_BUS"""
        assert resolve_bus('/api/v1/search/') == 'SEARCH_BUS'
        assert resolve_bus('/api/v1/analytics/') == 'SEARCH_BUS'
    
    def test_peer_mock_bus(self):
        """Peer mock paths should resolve to PEER_MOCK_BUS"""
        assert resolve_bus('/peer-mock-runtime/') == 'PEER_MOCK_BUS'
        assert resolve_bus('/api/mock/') == 'PEER_MOCK_BUS'
        assert resolve_bus('/simulator/test') == 'PEER_MOCK_BUS'
    
    def test_admin_bus(self):
        """Admin paths should resolve to ADMIN_BUS (consolidated)"""
        assert resolve_bus('/admin/') == 'ADMIN_BUS'
        assert resolve_bus('/staff/') == 'ADMIN_BUS'
        assert resolve_bus('/audit/') == 'ADMIN_BUS'
        assert resolve_bus('/ops/') == 'ADMIN_BUS'
        assert resolve_bus('/console/') == 'ADMIN_BUS'
    
    def test_public_web_bus(self):
        """Public web paths should resolve to PUBLIC_WEB_BUS"""
        assert resolve_bus('/') == 'PUBLIC_WEB_BUS'
        assert resolve_bus('/about') == 'PUBLIC_WEB_BUS'
        assert resolve_bus('/login') == 'PUBLIC_WEB_BUS'
    
    def test_unknown_bus(self):
        """Unknown API paths should return UNKNOWN (non-API paths go to PUBLIC_WEB_BUS)"""
        # Unknown API paths return UNKNOWN
        assert resolve_bus('/api/v99/future/') == 'UNKNOWN'
        assert resolve_bus('/api/unknown/') == 'UNKNOWN'
        
        # Unknown non-API paths default to PUBLIC_WEB_BUS
        assert resolve_bus('/unknown/path/') == 'PUBLIC_WEB_BUS'


class TestBusPowerState:
    """Test bus power state logic"""
    
    def test_kernel_core_bus_is_on(self):
        """KERNEL_CORE_BUS should be ON"""
        assert get_bus_state('KERNEL_CORE_BUS') == 'ON'
        assert is_bus_powered('KERNEL_CORE_BUS') is True
    
    def test_all_other_buses_are_off(self):
        """All non-kernel buses should be OFF in Phase-A (Canonical 8 Buses)"""
        off_buses = [
            'PUBLIC_WEB_BUS',
            'ADMIN_BUS',
            'AI_BUS',
            'PEER_MOCK_BUS',
            'MENTOR_BUS',
            'PAYMENT_BUS',
            'SEARCH_BUS',
        ]
        
        for bus in off_buses:
            assert get_bus_state(bus) == 'OFF', f'{bus} should be OFF'
            assert is_bus_powered(bus) is False, f'{bus} should not be powered'
    
    def test_unknown_bus_is_powered(self):
        """UNKNOWN bus should be powered (fail-open)"""
        assert is_bus_powered('UNKNOWN') is True
    
    def test_get_all_buses(self):
        """get_all_buses should return all bus states"""
        all_buses = get_all_buses()
        
        assert isinstance(all_buses, dict)
        assert all_buses['KERNEL_CORE_BUS'] == 'ON'
        assert all_buses['AI_BUS'] == 'OFF'
        assert len(all_buses) == len(BUS_POWER)


class TestPhaseAConstraints:
    """Test Phase-A specific constraints"""
    
    def test_only_kernel_is_on(self):
        """Phase-A: Only KERNEL_CORE_BUS should be ON"""
        all_buses = get_all_buses()
        on_buses = [bus for bus, state in all_buses.items() if state == 'ON']
        
        assert len(on_buses) == 1, 'Only one bus should be ON'
        assert on_buses[0] == 'KERNEL_CORE_BUS', 'Only KERNEL_CORE_BUS should be ON'
    
    def test_all_api_buses_are_off(self):
        """Phase-A: All API buses should be OFF"""
        api_paths = [
            '/api/v1/ai/',
            '/api/v1/mentors/',
            '/api/v1/payments/',
            '/api/v1/search/',
            '/api/v1/ats-signals/',
            '/api/v1/chat/',
            '/api/v1/signal-delivery/',
            '/api/v1/appointments/',
            '/api/v1/analytics/',
            '/api/engines/',
        ]
        
        for path in api_paths:
            bus = resolve_bus(path)
            assert is_bus_powered(bus) is False, f'{path} should be OFF (bus: {bus})'
    
    def test_admin_staff_buses_are_off(self):
        """Phase-A: Admin and Staff buses should be OFF (consolidated to ADMIN_BUS)"""
        assert is_bus_powered(resolve_bus('/admin/')) is False
        assert is_bus_powered(resolve_bus('/staff/')) is False
        assert is_bus_powered(resolve_bus('/audit/')) is False
        assert is_bus_powered(resolve_bus('/ops/')) is False
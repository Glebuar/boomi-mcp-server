"""
Component management category for Boomi MCP Server.

This category contains tools for managing Boomi components:
- Trading Partners (B2B/EDI)
- Processes (future)
- Connections (future)
- Maps (future)
- etc.
"""

from .trading_partners import (
    create_trading_partner,
    get_trading_partner,
    list_trading_partners,
    update_trading_partner,
    delete_trading_partner,
    analyze_trading_partner_usage,
    manage_trading_partner_action
)

__all__ = [
    'create_trading_partner',
    'get_trading_partner',
    'list_trading_partners',
    'update_trading_partner',
    'delete_trading_partner',
    'analyze_trading_partner_usage',
    'manage_trading_partner_action'
]

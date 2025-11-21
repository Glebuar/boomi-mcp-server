"""
Component management category for Boomi MCP Server.

This category contains tools for managing Boomi components:
- Trading Partners (B2B/EDI)
- Processes
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

from .processes import (
    list_processes,
    get_process,
    create_process,
    update_process,
    delete_process,
    manage_process_action
)

__all__ = [
    # Trading Partners
    'create_trading_partner',
    'get_trading_partner',
    'list_trading_partners',
    'update_trading_partner',
    'delete_trading_partner',
    'analyze_trading_partner_usage',
    'manage_trading_partner_action',
    # Processes
    'list_processes',
    'get_process',
    'create_process',
    'update_process',
    'delete_process',
    'manage_process_action'
]

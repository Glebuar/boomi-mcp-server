"""
Deployment & Configuration Category

Tools for deployment-time configuration:
- Trading partners (B2B/EDI)
- Deployment packages (future)
- Environment extensions (future)
- Process schedules (future)
"""

from .trading_partners import manage_trading_partner_action

__all__ = ['manage_trading_partner_action']

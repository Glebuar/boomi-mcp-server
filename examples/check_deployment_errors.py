#!/usr/bin/env python3
"""
Script to check recent deployments for errors and examine related audit logs.

This script:
1. Queries recent deployments (last 10-20)
2. Checks their status, especially looking for failed deployments
3. Gets detailed information about any errors
4. Queries audit logs for deployment-related events in the last 24-48 hours
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from boomi_mcp_client import MCPClient


class DeploymentErrorChecker:
    def __init__(self, server_url: str = "http://localhost:8080/sse"):
        """Initialize the deployment error checker."""
        self.client = MCPClient(server_url)
        
    def get_recent_deployments(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Query recent deployments."""
        print(f"\n🔍 Querying last {limit} deployments...")
        
        # Query deployments, ordered by deployedDate descending
        query = {
            "QueryFilter": {}
        }
        
        result = self.client.call_tool("query_deployments", query=query)
        
        if result.get("numberOfResults", 0) == 0:
            print("No deployments found.")
            return []
        
        deployments = result.get("result", [])
        
        # Sort by deployedDate descending and take the requested limit
        deployments.sort(key=lambda x: x.get("deployedDate", ""), reverse=True)
        return deployments[:limit]
    
    def check_deployment_status(self, deployments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize deployments by status."""
        status_groups = {
            "SUCCESS": [],
            "ERROR": [],
            "PARTIAL": [],
            "ABORTED": [],
            "DEPLOYING": [],
            "OTHER": []
        }
        
        for deployment in deployments:
            deployment_id = deployment.get("deploymentId", "Unknown")
            status = deployment.get("status", "UNKNOWN")
            
            # Get detailed deployment info
            try:
                detailed = self.client.call_tool("get_deployment", deployment_id=deployment_id)
                deployment["detailed_info"] = detailed
            except Exception as e:
                deployment["detailed_error"] = str(e)
            
            # Categorize by status
            if status in status_groups:
                status_groups[status].append(deployment)
            else:
                status_groups["OTHER"].append(deployment)
        
        return status_groups
    
    def get_deployment_error_details(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract error details from a failed deployment."""
        error_info = {
            "deployment_id": deployment.get("deploymentId"),
            "environment_id": deployment.get("environmentId"),
            "deployed_date": deployment.get("deployedDate"),
            "status": deployment.get("status"),
            "notes": deployment.get("notes", ""),
            "error_message": None,
            "package_info": {}
        }
        
        # Try to get package information
        package_id = deployment.get("packageId")
        if package_id:
            try:
                package_info = self.client.call_tool("get_package", package_id=package_id)
                error_info["package_info"] = {
                    "package_id": package_id,
                    "component_id": package_info.get("componentId"),
                    "package_version": package_info.get("packageVersion"),
                    "created_date": package_info.get("createdDate")
                }
            except Exception as e:
                error_info["package_error"] = str(e)
        
        # Extract error message from detailed info if available
        detailed = deployment.get("detailed_info", {})
        if detailed.get("error"):
            error_info["error_message"] = detailed.get("error")
        
        return error_info
    
    def get_deployment_audit_logs(self, hours_back: int = 48) -> List[Dict[str, Any]]:
        """Query audit logs for deployment-related events."""
        print(f"\n📋 Querying audit logs for deployment events in the last {hours_back} hours...")
        
        # Calculate the start time
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Query audit logs for deployment-related events
        query = {
            "QueryFilter": {
                "expression": {
                    "operator": "and",
                    "nestedExpression": [
                        {
                            "property": "date",
                            "operator": "GREATER_THAN_OR_EQUAL",
                            "argument": [start_time_str]
                        },
                        {
                            "property": "type",
                            "operator": "IN",
                            "argument": [
                                "deployment.created",
                                "deployment.completed", 
                                "deployment.failed",
                                "deployment.error",
                                "package.deployed",
                                "component.deployed"
                            ]
                        }
                    ]
                }
            }
        }
        
        try:
            result = self.client.call_tool("query_audit_logs", query=query)
            audit_logs = result.get("result", [])
            
            # If there are more results, fetch them
            query_token = result.get("queryToken")
            while query_token:
                try:
                    more_results = self.client.call_tool("query_audit_logs_more", token=query_token)
                    audit_logs.extend(more_results.get("result", []))
                    query_token = more_results.get("queryToken")
                except Exception:
                    break
            
            return audit_logs
        except Exception as e:
            print(f"Error querying audit logs: {e}")
            return []
    
    def generate_report(self):
        """Generate a comprehensive deployment error report."""
        print("=" * 80)
        print("BOOMI DEPLOYMENT ERROR REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Get recent deployments
        deployments = self.get_recent_deployments(limit=20)
        
        if not deployments:
            print("\nNo deployments found to analyze.")
            return
        
        # Check deployment status
        status_groups = self.check_deployment_status(deployments)
        
        # Print summary
        print("\n📊 DEPLOYMENT STATUS SUMMARY")
        print("-" * 40)
        for status, items in status_groups.items():
            if items:
                print(f"{status}: {len(items)} deployment(s)")
        
        # Detailed error analysis
        error_deployments = status_groups.get("ERROR", []) + status_groups.get("PARTIAL", [])
        
        if error_deployments:
            print("\n🚨 FAILED DEPLOYMENTS DETAILS")
            print("-" * 40)
            
            for idx, deployment in enumerate(error_deployments, 1):
                error_details = self.get_deployment_error_details(deployment)
                
                print(f"\n[{idx}] Deployment ID: {error_details['deployment_id']}")
                print(f"    Status: {error_details['status']}")
                print(f"    Date: {error_details['deployed_date']}")
                print(f"    Environment: {error_details['environment_id']}")
                
                if error_details['package_info']:
                    print(f"    Package: {error_details['package_info'].get('package_id')}")
                    print(f"    Component: {error_details['package_info'].get('component_id')}")
                    print(f"    Version: {error_details['package_info'].get('package_version')}")
                
                if error_details['error_message']:
                    print(f"    Error: {error_details['error_message']}")
                
                if error_details['notes']:
                    print(f"    Notes: {error_details['notes']}")
        
        # Get audit logs
        audit_logs = self.get_deployment_audit_logs(hours_back=48)
        
        if audit_logs:
            print("\n📝 DEPLOYMENT AUDIT LOGS (Last 48 hours)")
            print("-" * 40)
            print(f"Total audit entries: {len(audit_logs)}")
            
            # Group by type
            log_types = {}
            for log in audit_logs:
                log_type = log.get("type", "unknown")
                if log_type not in log_types:
                    log_types[log_type] = []
                log_types[log_type].append(log)
            
            print("\nAudit log breakdown by type:")
            for log_type, logs in log_types.items():
                print(f"  - {log_type}: {len(logs)} entries")
            
            # Show recent error entries
            error_logs = [log for log in audit_logs if "error" in log.get("type", "").lower() or "failed" in log.get("type", "").lower()]
            
            if error_logs:
                print(f"\n⚠️  Recent Error/Failed Audit Entries ({len(error_logs)} found):")
                for log in error_logs[:10]:  # Show max 10 recent errors
                    print(f"\n  Date: {log.get('date')}")
                    print(f"  Type: {log.get('type')}")
                    print(f"  User: {log.get('userId')}")
                    if log.get('message'):
                        print(f"  Message: {log.get('message')}")
                    if log.get('objectId'):
                        print(f"  Object ID: {log.get('objectId')}")


def main():
    """Main function to run the deployment error checker."""
    # Check if server URL is provided as argument
    server_url = "http://localhost:8080/sse"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"🔗 Connecting to Boomi MCP Server at: {server_url}")
    
    try:
        checker = DeploymentErrorChecker(server_url)
        checker.generate_report()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the Boomi MCP Server is running and accessible.")
        print("You can start it with: python -m boomi_mcp_server.server --transport sse --port 8080")
        sys.exit(1)


if __name__ == "__main__":
    main()
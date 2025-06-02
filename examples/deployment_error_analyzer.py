#!/usr/bin/env python3
"""
Advanced deployment error analyzer with detailed reporting and export capabilities.

Features:
- Query and analyze recent deployments
- Identify failed deployments with error details
- Cross-reference with audit logs
- Export results to JSON for further analysis
- Filter by date range, environment, or status
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from boomi_mcp_client import MCPClient


class DeploymentErrorAnalyzer:
    def __init__(self, server_url: str = "http://localhost:8080/sse"):
        """Initialize the analyzer."""
        self.client = MCPClient(server_url)
        self.results = {
            "analysis_date": datetime.now().isoformat(),
            "deployments": {},
            "audit_logs": [],
            "summary": {}
        }
    
    def query_deployments_by_date(self, days_back: int = 7, environment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query deployments within a date range."""
        start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        query = {
            "QueryFilter": {
                "expression": {
                    "operator": "and",
                    "nestedExpression": [
                        {
                            "property": "deployedDate",
                            "operator": "GREATER_THAN_OR_EQUAL",
                            "argument": [start_date]
                        }
                    ]
                }
            }
        }
        
        # Add environment filter if specified
        if environment_id:
            query["QueryFilter"]["expression"]["nestedExpression"].append({
                "property": "environmentId",
                "operator": "EQUALS",
                "argument": [environment_id]
            })
        
        try:
            result = self.client.call_tool("query_deployments", query=query)
            deployments = result.get("result", [])
            
            # Get all pages if there are more
            query_token = result.get("queryToken")
            while query_token:
                try:
                    more_results = self.client.call_tool("query_deployments_more", token=query_token)
                    deployments.extend(more_results.get("result", []))
                    query_token = more_results.get("queryToken")
                except Exception:
                    break
            
            return deployments
        except Exception as e:
            print(f"Error querying deployments: {e}")
            return []
    
    def analyze_deployment(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep analysis of a single deployment."""
        deployment_id = deployment.get("deploymentId")
        
        analysis = {
            "deployment_id": deployment_id,
            "status": deployment.get("status"),
            "deployed_date": deployment.get("deployedDate"),
            "environment_id": deployment.get("environmentId"),
            "package_id": deployment.get("packageId"),
            "notes": deployment.get("notes", ""),
            "errors": [],
            "warnings": [],
            "related_info": {}
        }
        
        # Get detailed deployment info
        try:
            detailed = self.client.call_tool("get_deployment", deployment_id=deployment_id)
            analysis["detailed_status"] = detailed.get("status")
            
            # Check for error information
            if detailed.get("error"):
                analysis["errors"].append({
                    "source": "deployment_details",
                    "message": detailed.get("error")
                })
        except Exception as e:
            analysis["warnings"].append(f"Could not fetch detailed info: {str(e)}")
        
        # Get package information
        if deployment.get("packageId"):
            try:
                package = self.client.call_tool("get_package", package_id=deployment.get("packageId"))
                analysis["related_info"]["package"] = {
                    "component_id": package.get("componentId"),
                    "version": package.get("packageVersion"),
                    "created_date": package.get("createdDate"),
                    "created_by": package.get("createdBy")
                }
                
                # Get component info
                if package.get("componentId"):
                    try:
                        component = self.client.call_tool("get_component", component_id=package.get("componentId"))
                        analysis["related_info"]["component"] = {
                            "name": component.get("name"),
                            "type": component.get("type"),
                            "sub_type": component.get("subType"),
                            "folder_id": component.get("folderId")
                        }
                    except Exception:
                        pass
            except Exception as e:
                analysis["warnings"].append(f"Could not fetch package info: {str(e)}")
        
        # Get environment info
        if deployment.get("environmentId"):
            try:
                environment = self.client.call_tool("get_environment", environment_id=deployment.get("environmentId"))
                analysis["related_info"]["environment"] = {
                    "name": environment.get("name"),
                    "classification": environment.get("classification")
                }
            except Exception:
                pass
        
        return analysis
    
    def get_related_audit_logs(self, deployment_id: str, time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """Get audit logs related to a specific deployment."""
        # We'll search for audit logs around the deployment time
        related_logs = []
        
        # Query audit logs that might reference this deployment
        query = {
            "QueryFilter": {
                "expression": {
                    "operator": "or",
                    "nestedExpression": [
                        {
                            "property": "objectId",
                            "operator": "EQUALS",
                            "argument": [deployment_id]
                        },
                        {
                            "property": "message",
                            "operator": "LIKE",
                            "argument": [f"%{deployment_id}%"]
                        }
                    ]
                }
            }
        }
        
        try:
            result = self.client.call_tool("query_audit_logs", query=query)
            related_logs = result.get("result", [])
        except Exception:
            pass
        
        return related_logs
    
    def analyze_all(self, days_back: int = 7, environment_id: Optional[str] = None, 
                    focus_on_errors: bool = True) -> Dict[str, Any]:
        """Perform complete analysis of deployments."""
        print(f"\n🔍 Analyzing deployments from the last {days_back} days...")
        
        # Get deployments
        deployments = self.query_deployments_by_date(days_back, environment_id)
        print(f"Found {len(deployments)} deployments")
        
        # Initialize counters
        status_counts = {}
        error_deployments = []
        
        # Analyze each deployment
        for deployment in deployments:
            status = deployment.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Perform detailed analysis for errors or all if not focusing on errors
            if not focus_on_errors or status in ["ERROR", "PARTIAL", "ABORTED"]:
                print(f"  Analyzing deployment {deployment.get('deploymentId')}...")
                analysis = self.analyze_deployment(deployment)
                
                # Get related audit logs for error deployments
                if status in ["ERROR", "PARTIAL", "ABORTED"]:
                    audit_logs = self.get_related_audit_logs(deployment.get("deploymentId"))
                    if audit_logs:
                        analysis["audit_logs"] = audit_logs
                    error_deployments.append(analysis)
                
                self.results["deployments"][deployment.get("deploymentId")] = analysis
        
        # Update summary
        self.results["summary"] = {
            "total_deployments": len(deployments),
            "date_range": f"Last {days_back} days",
            "environment_filter": environment_id or "All",
            "status_breakdown": status_counts,
            "error_count": len(error_deployments),
            "error_rate": f"{(len(error_deployments) / len(deployments) * 100):.1f}%" if deployments else "0%"
        }
        
        # Get general audit logs for deployment events
        self._fetch_general_audit_logs(days_back)
        
        return self.results
    
    def _fetch_general_audit_logs(self, days_back: int):
        """Fetch general deployment-related audit logs."""
        start_time = datetime.now(timezone.utc) - timedelta(days=days_back)
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
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
                            "operator": "LIKE",
                            "argument": ["deployment%"]
                        }
                    ]
                }
            }
        }
        
        try:
            result = self.client.call_tool("query_audit_logs", query=query)
            self.results["audit_logs"] = result.get("result", [])
        except Exception:
            pass
    
    def save_results(self, filename: str):
        """Save analysis results to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")
    
    def print_report(self):
        """Print a formatted report of the analysis."""
        print("\n" + "=" * 80)
        print("DEPLOYMENT ERROR ANALYSIS REPORT")
        print(f"Generated: {self.results['analysis_date']}")
        print("=" * 80)
        
        summary = self.results["summary"]
        print("\n📊 SUMMARY")
        print(f"  Total Deployments: {summary['total_deployments']}")
        print(f"  Date Range: {summary['date_range']}")
        print(f"  Environment: {summary['environment_filter']}")
        print(f"  Error Rate: {summary['error_rate']}")
        
        print("\n📈 STATUS BREAKDOWN")
        for status, count in summary["status_breakdown"].items():
            print(f"  {status}: {count}")
        
        # Print error details
        error_deployments = [d for d in self.results["deployments"].values() 
                           if d["status"] in ["ERROR", "PARTIAL", "ABORTED"]]
        
        if error_deployments:
            print(f"\n🚨 FAILED DEPLOYMENTS ({len(error_deployments)} found)")
            print("-" * 80)
            
            for deployment in error_deployments:
                print(f"\nDeployment ID: {deployment['deployment_id']}")
                print(f"  Status: {deployment['status']}")
                print(f"  Date: {deployment['deployed_date']}")
                print(f"  Environment: {deployment.get('related_info', {}).get('environment', {}).get('name', deployment['environment_id'])}")
                
                if deployment.get('related_info', {}).get('component'):
                    comp = deployment['related_info']['component']
                    print(f"  Component: {comp.get('name')} ({comp.get('type')})")
                
                if deployment['errors']:
                    print("  Errors:")
                    for error in deployment['errors']:
                        print(f"    - {error['message']}")
                
                if deployment.get('audit_logs'):
                    print(f"  Related Audit Logs: {len(deployment['audit_logs'])} entries")


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(description="Analyze Boomi deployment errors")
    parser.add_argument("--server", default="http://localhost:8080/sse",
                      help="MCP server URL (default: http://localhost:8080/sse)")
    parser.add_argument("--days", type=int, default=7,
                      help="Number of days to look back (default: 7)")
    parser.add_argument("--environment", help="Filter by environment ID")
    parser.add_argument("--output", help="Save results to JSON file")
    parser.add_argument("--all", action="store_true",
                      help="Analyze all deployments, not just errors")
    
    args = parser.parse_args()
    
    print(f"🔗 Connecting to Boomi MCP Server at: {args.server}")
    
    try:
        analyzer = DeploymentErrorAnalyzer(args.server)
        analyzer.analyze_all(
            days_back=args.days,
            environment_id=args.environment,
            focus_on_errors=not args.all
        )
        
        # Print report
        analyzer.print_report()
        
        # Save results if requested
        if args.output:
            analyzer.save_results(args.output)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the Boomi MCP Server is running and accessible.")
        print("You can start it with: python -m boomi_mcp_server.server --transport sse --port 8080")
        sys.exit(1)


if __name__ == "__main__":
    main()
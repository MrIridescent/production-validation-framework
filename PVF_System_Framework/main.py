#!/usr/bin/env python
"""
Production Validation Framework (PVF)
===================================

The main entry point for the Production Validation Framework.
This tool performs a comprehensive suite of validation tests to ensure
your application is 100% market-ready and production-grade.
"""

import os
import sys
import click
import logging
from validation_framework.validate_production_readiness import ProductionValidator

# Add current directory to path so we can import validation_framework
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

@click.command()
@click.option('--config', '-c', default='validation_framework/validation_config.json', help='Path to the validation configuration file')
@click.option('--report-path', '-r', default='./reports/validation_reports', help='Directory to save the validation reports')
@click.option('--url', '-u', help='Override API base URL from config')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(config, report_path, url, verbose):
    """Validate production readiness of your application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger("PVF-CLI")
    logger.info("Starting Production Validation Framework")
    
    try:
        validator = ProductionValidator(config)
        
        # Override URL if provided
        if url:
            validator.config["api_base_url"] = url
            
        results = validator.run_validations()
        html_report = validator.generate_report(report_path)
        
        summary = results["summary"]
        click.echo("\n" + "="*50)
        click.echo("VALIDATION SUMMARY")
        click.echo("="*50)
        click.echo(f"Total Tests:     {summary['total_tests']}")
        click.echo(f"Passed:          {summary['tests_passed']}")
        click.echo(f"Failed:          {summary['tests_failed']}")
        click.echo(f"Warnings:        {summary['tests_warned']}")
        click.echo(f"Pass Percentage: {summary['pass_percentage']:.1f}%")
        click.echo("-" * 50)
        
        if summary["production_ready"]:
            click.secho("STATUS: PRODUCTION READY ✅", fg='green', bold=True)
            exit_code = 0
        else:
            click.secho("STATUS: NOT PRODUCTION READY ❌", fg='red', bold=True)
            exit_code = 1
            
        click.echo(f"\nDetailed report available at: {html_report}")
        sys.exit(exit_code)
        
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg='red', bold=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

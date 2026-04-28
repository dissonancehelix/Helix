<?php
# =============================================================================
# Trails Database — LocalSettings additions
# Append to /var/www/html/wiki/LocalSettings.php
# =============================================================================

# -----------------------------------------------------------------------------
# Site identity
# -----------------------------------------------------------------------------
$wgSitename = "Trails Database";
$wgMetaNamespace = "Trails_Database";

# Disable public registration — this is a private single-user wiki
$wgGroupPermissions['*']['createaccount'] = false;
$wgGroupPermissions['*']['read'] = true;  # change to false to make fully private

# -----------------------------------------------------------------------------
# Custom namespaces
# -----------------------------------------------------------------------------
# IDs 100+ are available for custom namespaces (even = content, odd = talk)
define( 'NS_METADATA',       100 );
define( 'NS_METADATA_TALK',  101 );
define( 'NS_DRAFT',          102 );
define( 'NS_DRAFT_TALK',     103 );
define( 'NS_SCHEMA',         104 );
define( 'NS_SCHEMA_TALK',    105 );

$wgExtraNamespaces[NS_METADATA]      = 'Metadata';
$wgExtraNamespaces[NS_METADATA_TALK] = 'Metadata_talk';
$wgExtraNamespaces[NS_DRAFT]         = 'Draft';
$wgExtraNamespaces[NS_DRAFT_TALK]    = 'Draft_talk';
$wgExtraNamespaces[NS_SCHEMA]        = 'Schema';
$wgExtraNamespaces[NS_SCHEMA_TALK]   = 'Schema_talk';

# Form: and Module: namespaces are provided by Page Forms and Scribunto respectively

# Make Draft: namespace searchable but not indexed
$wgNamespacesToBeSearchedDefault[NS_DRAFT] = false;

# -----------------------------------------------------------------------------
# Extensions
# (Uncomment each block after installing the extension into extensions/)
# -----------------------------------------------------------------------------

# -- Cargo --
# wfLoadExtension( 'Cargo' );

# -- Page Forms --
# wfLoadExtension( 'PageForms' );

# -- Page Schemas --
# wfLoadExtension( 'PageSchemas' );

# -- Scribunto (Lua modules) --
# wfLoadExtension( 'Scribunto' );
# $wgScribuntoDefaultEngine = 'luastandalone';

# -- Approved Revs --
# wfLoadExtension( 'ApprovedRevs' );
# $egApprovedRevsAutomaticApprovals = false;
# # Who can approve revisions:
# $wgGroupPermissions['sysop']['approverevisions'] = true;

# -- AbuseFilter --
# wfLoadExtension( 'AbuseFilter' );
# $wgAbuseFilterActions['block'] = false;  # structural integrity only, no blocking
# $wgGroupPermissions['sysop']['abusefilter-modify'] = true;
# $wgGroupPermissions['*']['abusefilter-view'] = false;

# -- TemplateData --
# wfLoadExtension( 'TemplateData' );

# -----------------------------------------------------------------------------
# File uploads (disabled until configured)
# -----------------------------------------------------------------------------
$wgEnableUploads = false;

# -----------------------------------------------------------------------------
# Short URLs (optional — uncomment if .htaccess rewriting is configured)
# -----------------------------------------------------------------------------
# $wgArticlePath = '/wiki/$1';
# $wgUsePathInfo = true;

# -----------------------------------------------------------------------------
# Cargo: Trails Database table prefix (set after Cargo is enabled)
# -----------------------------------------------------------------------------
# $wgCargoDBtype    = 'mysql';
# $wgCargoDBserver  = '127.0.0.1';
# $wgCargoDBname    = 'trails_wiki';
# $wgCargoDBuser    = 'wiki_user';
# $wgCargoDBpassword = 'trailsdb2026';

# =============================================================================
# END Trails Database additions
# =============================================================================

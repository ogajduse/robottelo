"""Tests for leapp upgrade of content hosts with Satellite

:Requirement: leapp

:CaseLevel: Integration

:CaseComponent: LeappIntegration

:Team: Rocket

:TestType: Functional

:CaseImportance: High

:CaseAutomation: Automated

:Upstream: No
"""
import pytest
from packaging.version import Version

from robottelo.hosts import ContentHost
from robottelo.logging import logger

synced_repos = pytest.StashKey[dict]


@pytest.fixture(scope='module')
def module_stash(request):
    """Module scoped stash for storing data between tests"""
    # Please refer the documentation for more details on stash
    # https://docs.pytest.org/en/latest/reference/reference.html#stash
    request.node.stash[synced_repos] = {}
    yield request.node.stash


RHEL_REPOS = {
    'rhel7_9_server': {
        'id': 'rhel-7-server-rpms',
        'name': 'Red Hat Enterprise Linux 7 Server RPMs x86_64 7.9',
        'releasever': '7.9',
        'reposet': 'Red Hat Enterprise Linux 7 Server (RPMs)',
        'product': 'Red Hat Enterprise Linux Server',
    },
    'rhel7_server_extras': {
        'id': 'rhel-7-server-extras-rpms',
        'name': 'Red Hat Enterprise Linux 7 Server - Extras RPMs x86_64',
        'releasever': '7',
        'reposet': 'Red Hat Enterprise Linux 7 Server - Extras (RPMs)',
        'product': 'Red Hat Enterprise Linux Server',
    },
    'rhel8_8_bos': {
        'id': 'rhel-8-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS RPMs 8.8',
        'releasever': '8.8',
        'reposet': 'Red Hat Enterprise Linux 8 for x86_64 - BaseOS (RPMs)',
    },
    'rhel8_8_aps': {
        'id': 'rhel-8-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream RPMs 8.8',
        'releasever': '8.8',
        'reposet': 'Red Hat Enterprise Linux 8 for x86_64 - AppStream (RPMs)',
    },
    'rhel9_2_bos': {
        'id': 'rhel-9-for-x86_64-baseos-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS RPMs 9.2',
        'releasever': '9.2',
        'reposet': 'Red Hat Enterprise Linux 9 for x86_64 - BaseOS (RPMs)',
    },
    'rhel9_2_aps': {
        'id': 'rhel-9-for-x86_64-appstream-rpms',
        'name': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream RPMs 9.2',
        'releasever': '9.2',
        'reposet': 'Red Hat Enterprise Linux 9 for x86_64 - AppStream (RPMs)',
    },
}


@pytest.fixture(scope='module')
def module_leapp_org(module_target_sat):
    logger.info('Creating Leapp Organization')
    return "org"


@pytest.fixture
def function_leapp_cv():
    logger.info('Creating Leapp Content View')
    return "cv"


@pytest.fixture(scope='module')
def module_leapp_lce(module_target_sat, module_leapp_org):
    logger.info('Creating Leapp Lifecycle Environment')
    return "lce"


@pytest.fixture
def function_leapp_ak(
    module_target_sat, function_leapp_cv, module_leapp_lce, module_leapp_org, upgrade_path
):
    logger.info(
        'Creating Leapp Activation Key for RHEL %s -> %s',
        upgrade_path['source_version'],
        upgrade_path['target_version'],
    )
    return "ak"


@pytest.fixture
def register_host_with_satellite(
    module_target_sat, custom_leapp_host, module_leapp_org, function_leapp_ak
):
    logger.info(
        'Registering Leapp Host with Satellite - RHEL %s', custom_leapp_host.os_version.major
    )
    return "registered"


@pytest.fixture
def precondition_check_upgrade_and_install_leapp_tool(custom_leapp_host):
    """Clean-up directory if in-place upgrade already performed,
    set rhel release version, update system and install leapp tool"""
    source_rhel_minor_ver = custom_leapp_host.os_version.major
    logger.info(
        'Running precondition check for upgrade and install leapp tool - RHEL %s',
        source_rhel_minor_ver,
    )


@pytest.fixture
def fix_inhibitors(custom_leapp_host):
    """Fix inhibitors to avoid hard stop of Leapp tool execution"""
    source_rhel_minor_ver = custom_leapp_host.os_version.major
    logger.info('Fixing inhibitors for source rhel version %s', source_rhel_minor_ver)


@pytest.fixture
def leapp_sat_content(
    module_stash,
    custom_leapp_host,
    upgrade_path,
    module_target_sat,
    module_leapp_org,
    function_leapp_cv,
    module_leapp_lce,
):
    """Enable rhel bos, aps repository and add it to the content view"""
    source = custom_leapp_host.os_version
    target = upgrade_path['target_version']
    all_repos = []
    logger.info('Enabling repositories for RHEL %s -> %s', source, target)
    for rh_repo_key in RHEL_REPOS.keys():
        release_version = RHEL_REPOS[rh_repo_key]['releasever']
        if release_version in str(source) or release_version in target:
            prod = rh_repo_key.split('_')[0]
            if module_stash[synced_repos].get(rh_repo_key, None):
                logger.info("Repo %s already synced, not syncing it", rh_repo_key)
            else:
                logger.info('Enabling %s repository in product %s', rh_repo_key, prod)
                logger.info('Syncing %s repository', rh_repo_key)
                module_stash[synced_repos][rh_repo_key] = True
            all_repos.append(rh_repo_key)
    logger.info('Repos to be added to the AK: %s', all_repos)
    logger.info('Assigning repositories to content view')
    # Publish, promote content view to lce
    logger.info('Publishing content view')
    logger.info('Promoting content view to lifecycle environment')


@pytest.fixture
def custom_leapp_host(upgrade_path):
    deploy_args = {}
    deploy_args['deploy_rhel_version'] = upgrade_path['source_version']
    logger.info('Creating Leapp Host - RHEL %s', deploy_args)
    chost = ContentHost('foo.bar')
    chost.__dict__.update({'os_version': Version(upgrade_path['source_version'])})
    return chost


@pytest.mark.parametrize(
    'upgrade_path',
    [
        {'source_version': '7.9', 'target_version': '8.8'},
        {'source_version': '8.8', 'target_version': '9.2'},
    ],
    ids=lambda upgrade_path: f'{upgrade_path["source_version"]}_to_{upgrade_path["target_version"]}',
)
@pytest.mark.usefixtures(
    'leapp_sat_content',
    'register_host_with_satellite',
    'precondition_check_upgrade_and_install_leapp_tool',
    'fix_inhibitors',
)
def test_leapp_upgrade_rhel(
    module_target_sat,
    custom_leapp_host,
    upgrade_path,
):
    """Test to upgrade RHEL host to next major RHEL Realse with Leapp Preupgrade and Leapp Upgrade
    Job templates

    :id: 8eccc689-3bea-4182-84f3-c121e95d54c3

    :Steps:
        1. Import a subscription manifest and enable, sync source & target repositories
        2. Create LCE, Create CV, add repositories to it, publish and promote CV, Create AK, etc.
        3. Register content host with AK
        4. Varify target rhel repositories are enable on Satellite
        5. Update all packages, install leapp tool and fix inhibitors
        6. Run Leapp Preupgrade and Leapp Upgrade job template

    :expectedresults:
        1. Update RHEL OS major version to another major version

    """
    logger.info('Running test for upgrade path %s', upgrade_path)

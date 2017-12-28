"""
CLI Entrypoint
"""
import click
from fest import __version__
from fest import graph as facebook


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(__version__, '-v', '--version')
@click.option('--facebook-app-id',
              envvar='FACEBOOK_APP_ID',
              help='Optional facebook app ID')
@click.option('--facebook-app-secret',
              envvar='FACEBOOK_APP_SECRET',
              help='Optional facebook app secret')
@click.pass_context
def fest(ctx, facebook_app_id, facebook_app_secret):
    """ Export Facebook Page Events to other services.

        See https://github.com/amancevice/fest for details & instructions.
    """
    ctx.obj = {}
    ctx.obj['graph'] = facebook.GraphAPI(app_id=facebook_app_id,
                                         app_secret=facebook_app_secret)


@fest.group('google')
@click.option('--google-account-type',
              envvar='GOOGLE_ACCOUNT_TYPE',
              help='Optional Google service account type')
@click.option('--google-client-email',
              envvar='GOOGLE_CLIENT_EMAIL',
              help='Optional Google service client email')
@click.option('--google-client-id',
              envvar='GOOGLE_CLIENT_ID',
              help='Optional Google service client ID')
@click.option('--google-private-key',
              envvar='GOOGLE_PRIVATE_KEY',
              help='Optional Google service private key')
@click.option('--google-private-key-id',
              envvar='GOOGLE_PRIVATE_KEY_ID',
              help='Optional Google service private key ID')
@click.option('--google-scope',
              envvar='GOOGLE_SCOPE',
              help='Optional Google service scope')
@click.pass_context
def fest_google(ctx, google_account_type, google_client_email,
                google_client_id, google_private_key, google_private_key_id,
                google_scope):
    """ Connect to Google Cloud. """
    # pylint: disable=too-many-arguments
    from fest import google
    ctx.obj['cloud'] = google.GoogleCloud.from_credentials(
        scopes=[google_scope],
        service_type=google_account_type,
        private_key_id=google_private_key_id,
        private_key=google_private_key,
        client_email=google_client_email,
        client_id=google_client_id)


@fest.group('tribe')
@click.option('--tribe-endpoint',
              envvar='TRIBE_ENDPOINT',
              help='Optional tribe REST API endpoint')
@click.option('--wordpress-endpoint',
              envvar='WORDPRESS_ENDPOINT',
              help='Optional wordpress endpoint')
@click.option('--wordpress-username',
              envvar='WORDPRESS_USERNAME',
              help='Optional wordpress username')
@click.option('--wordpress-app-password',
              envvar='WORDPRESS_APP_PASSWORD',
              help='Optional WordPress app password')
@click.pass_context
def fest_tribe(ctx, tribe_endpoint, wordpress_endpoint, wordpress_username,
               wordpress_app_password):
    """ Connect to Tribe. """
    from fest import tribe
    wordpress = tribe.WordPress(url=wordpress_endpoint,
                                username=wordpress_username,
                                password=wordpress_app_password)
    ctx.obj['tribe'] = tribe.TribeCalendar(wordpress, tribe_endpoint)


@fest_google.command('clear')
@click.option('-f', '--force',
              default=False,
              help='Do not prompt before clearing',
              is_flag=True,
              prompt='Are you sure?')
@click.option('-g', '--google-id',
              envvar='GOOGLE_CALENDAR_ID',
              help='Google Calendar ID')
@click.pass_context
def fest_google_clear(ctx, force, google_id):
    """ Clear a linked Google Calendar. """
    gcal = ctx.obj['cloud'].get_calendar(google_id)
    if force is True:
        gcal.clear_events()


@fest_google.command('create')
@click.option('-f', '--facebook-id',
              envvar='FACEBOOK_PAGE_ID',
              help='Facebook Page ID')
@click.option('-z', '--tz',
              required=True,
              help='Time zone of calendar')
@click.pass_context
def fest_google_create(ctx, facebook_id, tz):
    """ Create a new Google Calendar. """
    # pylint: disable=invalid-name,unused-variable
    page = ctx.obj['graph'].get_page(facebook_id)
    gcal = ctx.obj['cloud'].create_calendar(page, tz)
    click.echo(gcal['id'])


@fest_google.command('destroy')
@click.option('-f', '--force',
              default=False,
              help='Do not prompt before destroying',
              is_flag=True,
              prompt='Are you sure?')
@click.option('-g', '--google-id',
              envvar='GOOGLE_CALENDAR_ID',
              help='Google Calendar ID')
@click.pass_context
def fest_google_destroy(ctx, force, google_id):
    """ Create a new Google Calendar. """
    if force is True:
        ctx.obj['cloud'].delete_calendar(google_id)


@fest_google.command('share')
@click.option('-e', '--email', help='Email of new owner for calendar')
@click.option('-g', '--google-id',
              envvar='GOOGLE_CALENDAR_ID',
              help='Google Calendar ID')
@click.pass_context
def fest_google_share(ctx, email, google_id):
    """ Grant ownership of Google Calendar to user. """
    gcal = ctx.obj['cloud'].get_calendar(google_id)
    gcal.add_owner(email)


@fest_google.command('shell')
@click.pass_context
def fest_google_shell(ctx):
    """ Sync a facebook page. """
    # pylint: disable=unused-variable
    try:
        import IPython
        cloud = ctx.obj['cloud']
        graph = ctx.obj['graph']
        IPython.embed()
    except ImportError:
        click.echo('Please install IPython to use the shell.')


@fest_google.command('sync')
@click.option('-f', '--facebook-id',
              envvar='FACEBOOK_PAGE_ID',
              help='Facebook Page ID')
@click.option('-g', '--google-id',
              envvar='GOOGLE_CALENDAR_ID',
              help='Google Calendar ID')
@click.option('-a', '--sync-all',
              help='Sync all events, not just upcoming',
              is_flag=True)
@click.pass_context
def fest_google_sync(ctx, facebook_id, google_id, sync_all):
    """ Sync a facebook page. """
    click.echo('Fetching Google Calendar: {}'.format(google_id))
    gcal = ctx.obj['cloud'].get_calendar(google_id)

    click.echo('Fetching Facebook Events: {}'.format(facebook_id))
    page = ctx.obj['graph'].get_page(facebook_id)
    time_filter = None if sync_all else 'upcoming'
    events = page.get_events(time_filter=time_filter)

    click.echo('Synchronizing Events')
    gcal.sync_events(*events)


@fest_tribe.command('shell')
@click.pass_context
def fest_tribe_shell(ctx):
    """ Sync a facebook page. """
    # pylint: disable=unused-variable
    try:
        import IPython
        graph = ctx.obj['graph']
        tribe = ctx.obj['tribe']
        IPython.embed()
    except ImportError:
        click.echo('Please install IPython to use the shell.')


@fest_tribe.command('sync')
@click.option('-f', '--facebook-id',
              envvar='FACEBOOK_PAGE_ID',
              help='Facebook Page ID')
@click.option('-a', '--sync-all',
              help='Sync all events, not just upcoming',
              is_flag=True)
@click.pass_context
def fest_tribe_sync(ctx, facebook_id, sync_all):
    """ Sync a facebook page. """
    click.echo('Fetching Tribe Calendar')
    tribe = ctx.obj['tribe']

    click.echo('Fetching Facebook Events: {}'.format(facebook_id))
    page = ctx.obj['graph'].get_page(facebook_id)
    time_filter = None if sync_all else 'upcoming'
    events = page.get_events(time_filter=time_filter)

    click.echo('Synchronizing Events')
    tribe.sync_events(*events)


if __name__ == '__main__':
    fest()  # pylint: disable=no-value-for-parameter

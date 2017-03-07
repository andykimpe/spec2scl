import argparse
import sys

from spec2scl.convertor import Convertor


def get_parser():
    """Return an argument parser for CLIcommand."""
    parser = argparse.ArgumentParser(description='Convert RPM specfile to be SCL ready.')
    parser.add_argument(
        'specfiles',
        help='Paths to the specfiles or name of the meta package, see --meta-specfile.',
        metavar='ARGUMENT',
        nargs='*',
    )
    parser.add_argument(
        '-i',
        help='Convert in place (replaces old specfiles with the new generated ones).'
             ' Mandatory when multiple specfiles are to be converted.',
        required=False,
        action='store_true'
    )
    parser.add_argument(
        '-r', '--no-meta-runtime-dep',
        required=False,
        help='Don\'t add the runtime dependency on the scl runtime package.',
        action='store_true'
    )
    parser.add_argument(
        '-b', '--no-meta-buildtime-dep',
        required=False,
        help='Don\'t add the buildtime dependency on the scl runtime package.',
        action='store_true'
    )
    parser.add_argument(
        '-k', '--skip-functions',
        required=False,
        default="",
        help='Comma separated list of transformer functions to skip',
    )

    grp = parser.add_mutually_exclusive_group(required=False)
    grp.add_argument(
        '-n', '--no-deps-convert',
        required=False,
        help='Don\'t convert dependency tags (mutually exclusive with -l).',
        action='store_true',
    )
    grp.add_argument(
        '-l', '--list-file',
        required=False,
        help='List of the packages/provides, that will be in the SCL '
             '(to convert Requires/BuildRequires properly). Lines in '
             'the file are in form of "pkg-name %%{?custom_prefix}", '
             'where the prefix part is optional.',
        metavar='SCL_CONTENTS_LIST'
    )

    meta_group = parser.add_argument_group(title='metapackage optional arguments')
    meta_group.add_argument(
        '--meta-specfile',
        required=False,
        help='If used, spec2scl will produce metapackage specfile based on, '
             'the metapackage name provided, see SCL docs for metapackage naming.',
        metavar='METAPACKAGE_NAME'
    )
    meta_group.add_argument(
        '-v', '--variables',
        required=False,
        default="",
        help='List of variables separated with comma, used only with'
             ' --meta-specfile option',
    )
    return parser


def main(args=None):
    """Main CLI entry point."""
    parser = get_parser()
    args = parser.parse_args(args)

    if len(args.specfiles) > 1 and not args.i:
        parser.error('You can only convert more specfiles using -i (in place) mode.')

    if len(args.specfiles) == 0 and sys.stdin.isatty() and not args.meta_specfile:
        parser.error('You must either specify specfile(s) or reading from stdin.')

    args.skip_functions = args.skip_functions.split(',')
    convertor = Convertor(options=vars(args))
    try:
        convertor.handle_scl_deps()
    except IOError as e:
        print('Could not open file: {0}'.format(e))
        sys.exit(1)

    # Produce a metapackage specfile.
    if args.meta_specfile:
        meta_specfile = convertor.create_meta_specfile()
        print(meta_specfile)
        return

    specs = []
    # Convert a single specfile from stdin.
    if len(args.specfiles) == 0 and not sys.stdin.isatty():
        specs.append(sys.stdin.readlines())

    # Convert specfiles passed as arguments.
    for specfile in args.specfiles:
        try:
            with open(specfile) as f:
                specs.append(f.readlines())
        except IOError as e:
            print('Could not open file: {0}'.format(e))
            sys.exit(1)

    for i, spec in enumerate(specs):
        converted = convertor.convert(spec)
        if not args.i or not args.specfiles:
            print(converted)
        else:
            try:
                f = open(args.specfiles[i], 'w')
                f.write(str(converted))
            except IOError as e:
                print('Could not open file: {0}'.format(e))
            else:
                f.close()

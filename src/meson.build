pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'pe')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'ui/main_view.blp',
    'ui/gui.blp',
    'ui/about.blp',
    'ui/pin_entry.blp',
    'ui/success_view.blp',
    'ui/transaction_view.blp',
    'ui/menu_button.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('pe',
  'pe.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
if get_option('profile') == 'testing'
  conf.set('TESTING', '1')
else
  conf.set('TESTING', '0')
endif
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'pe.in',
  output: 'pe',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

pe_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'utils.py',
  'utils_testing.py',
  'pin_entry.py',
  'success_view.py',
  'transaction_view.py',
  'menu_button.py',
  'address_widgets.py'
]

install_data(pe_sources, install_dir: moduledir)
from setuptools import setup
import os


if os.path.isfile('requirements.txt'):
    with open('requirements.txt', 'r') as requirements_file:
        install_requires = requirements_file.read().splitlines()
    for package in install_requires:
        if package.startswith('git'):
            pname = package.split('/')[-1].split('.')[0]
            install_requires[install_requires.index(package)] = pname + ' @ ' + package

setup(
    name='flex_maldi_dda_automation',
    version='0.4.0b0',
    url='https://github.com/gtluu/flex_maldi_dda_automation',
    license='Apache License',
    author='Gordon T. Luu',
    author_email='gtluu912@gmail.com',
    packages=['msms_autox_generator'],
    include_package_data=True,
    package_data={'': ['*.cfg']},
    description='timsTOF fleX MALDI AutoXecute Automation Scripts',
    #entry_points={'console_scripts': ['process_maldi_dda=msms_autox_generator.run:main']},
    install_requires=install_requires,
    setup_requires=install_requires
)

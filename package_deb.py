import os
import shutil
import subprocess
import sys

def run_command(command):
    print(f"Running: {command}")
    subprocess.check_call(command, shell=True)

def main():
    app_name = "pdfbooklet"
    version = "3.1.7"
    arch = "all"
    package_name = f"{app_name}_{version}_{arch}"
    build_dir = os.path.abspath("build_deb")
    pkg_dir = os.path.join(build_dir, app_name)
    
    # Clean up
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(pkg_dir)
    
    # Install to temporary root
    print("Installing to temporary root...")
    # Use --prefix=/usr and --install-layout=deb for Debian packaging
    # This ensures it goes to /usr/lib/python3/dist-packages
    run_command(f"{sys.executable} setup.py install --root={pkg_dir} --prefix=/usr --install-layout=deb --no-compile")
    
    # Create DEBIAN directory
    debian_dir = os.path.join(pkg_dir, "DEBIAN")
    os.makedirs(debian_dir)
    
    # Create control file
    control_content = f"""Package: {app_name}
Version: {version}
Section: utils
Priority: optional
Architecture: {arch}
Depends: python3, python3-gi, python3-gi-cairo, python3-cairo, python3-pikepdf, python3-dateutil, python3-packaging, gir1.2-gtk-3.0, gir1.2-poppler-0.18
Recommends: gir1.2-handy-1
Maintainer: Tomas Julian Resquin <tomasjulianresquin@proton.me>
Description: A simple application for creating booklets and other layouts from PDF files
 PdfBooklet is a GTK+ based utility to create booklets and other layouts 
 from PDF documents.
"""
    with open(os.path.join(debian_dir, "control"), "w") as f:
        f.write(control_content)
        
    # Create postinst script to fix permissions if needed (as seen in build.py)
    postinst_content = f"""#!/bin/sh
set -e
# Fix permissions for data directory if needed
if [ -d /usr/share/pdfbooklet ]; then
    chmod -R 755 /usr/share/pdfbooklet
fi
"""
    postinst_path = os.path.join(debian_dir, "postinst")
    with open(postinst_path, "w") as f:
        f.write(postinst_content)
    os.chmod(postinst_path, 0o755)

    # Build the package
    print("Building .deb package...")
    final_builds_dir = os.path.abspath("builds")
    if not os.path.exists(final_builds_dir):
        os.makedirs(final_builds_dir)
        
    output_deb_path = os.path.join(final_builds_dir, f"{package_name}.deb")
    
    # If building on a mounted NTFS filesystem (like WSL /mnt/c), permissions are often 777,
    # which causes dpkg-deb to reject the control directory. We copy to /tmp to build safely.
    if "/mnt/" in pkg_dir:
        tmp_build = f"/tmp/{package_name}_deb"
        if os.path.exists(tmp_build):
            shutil.rmtree(tmp_build)
        shutil.copytree(pkg_dir, tmp_build)
        run_command(f"chmod -R 0755 {tmp_build}")
        run_command(f"dpkg-deb --root-owner-group --build {tmp_build} {output_deb_path}")
        shutil.rmtree(tmp_build)
    else:
        run_command(f"dpkg-deb --root-owner-group --build {pkg_dir} {output_deb_path}")
    
    print(f"Package built successfully: {output_deb_path}")
    print(f"File generated in: builds/{package_name}.deb")

if __name__ == "__main__":
    main()

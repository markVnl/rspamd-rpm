%global rspamd_user _rspamd

Name:             rspamd
Version:          1.9.4
Release:          2.2%{?dist}
Summary:          Rapid spam filtering system
License:          ASL 2.0 and LGPLv3 and BSD and MIT and CC0 and zlib
URL:              https://www.rspamd.com/
Source0:          https://github.com/vstakhov/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:          80-rspamd.preset

Source3:          rspamd.logrotate

Patch0:           rspamd-secure-ssl-ciphers.patch

# technically not true if you opt-out of hyperscan on el7.x86_64
%if 0%{?rhel} == 7
ExclusiveArch:    %{arm} aarch64
%endif

BuildRequires:    cmake
BuildRequires:    file-devel
BuildRequires:    gd-devel
BuildRequires:    glib2-devel
%ifarch x86_64
%if 0%{?rhel} > 7
BuildRequires:    hyperscan-devel
%endif
%endif
BuildRequires:    jemalloc-devel
BuildRequires:    libaio-devel
BuildRequires:    libcurl-devel
BuildRequires:    libevent-devel
BuildRequires:    libicu-devel
%if 0%{?rhel} > 7
BuildRequires:    libnsl2-devel
%endif
BuildRequires:    libunwind-devel
%ifarch ppc64 ppc64le aarch64
BuildRequires:    lua-devel
%else
BuildRequires:    luajit-devel
%endif
%ifarch %{arm} x86_64
BuildRequires:    openblas-devel
%endif
BuildRequires:    openssl-devel
BuildRequires:    pcre2-devel
BuildRequires:    perl
BuildRequires:    perl-Digest-MD5
BuildRequires:    ragel
BuildRequires:    sqlite-devel
%{?systemd_requires}
Requires:         logrotate

# Bundled dependencies
# TODO: Check for bundled js libs
# TODO: Add explicit bundled lib versions where known
# TODO: Unbundle deps where possible
# TODO: Double-check Provides
# aho-corasick: LGPL-3.0
Provides: bundled(aho-corasick)
# cdb: Public Domain
Provides: bundled(cdb) = 1.1.0
# hiredis: BSD-3-Clause
Provides: bundled(hiredis) = 0.13.3
# lc-btrie: BSD-3-Clause
Provides: bundled(lc-btrie)
# libottery: CC0
Provides: bundled(libottery)
# librdns: BSD-2-Clause
Provides: bundled(librdns)
# libucl: BSD-2-Clause
Provides: bundled(libucl)
# linenoise: BSD-2-Clause
Provides: bundled(linenoise) = 1.0
# lua-argparse: MIT
Provides: bundled(lua-argparse)
# lua-fun: MIT
Provides: bundled(lua-fun)
# lua-lpeg: MIT
Provides: bundled(lua-lpeg) = 1.0
# lua-moses: MIT
Provides: bundled(lua-moses)
# lua-tableshape: MIT
Provides: bundled(lua-tableshape) = ae67256
# lua-torch: Apache-2.0 or BSD-3-Clause
Provides: bundled(lua-torch)
# mumhash: MIT
Provides: bundled(mumhash)
# ngx-http-parser: MIT
Provides: bundled(ngx-http-parser) = 2.2.0
# perl-Mozilla-PublicSuffix: MIT
Provides: bundled(perl-Mozilla-PublicSuffix)
# snowball: BSD-3-Clause
Provides: bundled(snowball)
# t1ha: Zlib
Provides: bundled(t1ha)
# uthash: BSD
Provides: bundled(uthash) = 1.9.8
# xxhash: BSD
Provides: bundled(xxhash)
# zstd: BSD
Provides: bundled(zstd) = 1.3.1

%description
Rspamd is a rapid, modular and lightweight spam filter. It is designed to work
with big amount of mail and can be easily extended with own filters written in
lua.

%prep
%setup -q
%patch0 -p1
rm -rf centos
rm -rf debian
rm -rf docker
rm -rf freebsd

%build
# NOTE: To disable tests during build, set DEBIAN_BUILD=1 option
%cmake \
  -DDEBIAN_BUILD=0 \
  -DCONFDIR=%{_sysconfdir}/%{name} \
  -DMANDIR=%{_mandir} \
  -DDBDIR=%{_sharedstatedir}/%{name} \
  -DRUNDIR=%{_localstatedir}/run/%{name} \
  -DLOGDIR=%{_localstatedir}/log/%{name} \
  -DSHAREDIR=%{_datadir}/%{name} \
  -DLIBDIR=%{_libdir}/%{name}/ \
  -DSYSTEMDDIR=%{_unitdir} \
  -DENABLE_GD=ON \
%ifarch x86_64
%if 0%{?rhel} > 7
  -DENABLE_HYPERSCAN=ON \
%endif
%endif
  -DENABLE_JEMALLOC=ON \
  -DENABLE_LIBUNWIND=ON \
%ifarch ppc64 ppc64le aarch64
  -DENABLE_LUAJIT=OFF \
  -DENABLE_TORCH=OFF \
%endif
  -DENABLE_PCRE2=ON \
  -DENABLE_URL_INCLUDE=ON \
  -DRSPAMD_USER=%{rspamd_user} \
  -DRSPAMD_GROUP=%{rspamd_user} \
  -DWANT_SYSTEMD_UNITS=ON
%make_build


%install
%{make_install} DESTDIR=%{buildroot} INSTALLDIRS=vendor
# The tests install some files we don't want so ship
rm -f %{buildroot}%{_libdir}/debug/usr/bin/rspam*
install -Ddpm 0755 %{buildroot}%{_sysconfdir}/%{name}/{local,override}.d/
install -Ddpm 0755 0755 %{buildroot}%{_sharedstatedir}/%{name}
install -Dpm 0644 %{SOURCE1} %{buildroot}%{_presetdir}/80-rspamd.preset
install -Dpm 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/rspamd
install -Dpm 0644 LICENSE.md %{buildroot}%{_docdir}/licenses/LICENSE.md


%pre
%{_sbindir}/groupadd -r %{rspamd_user} 2>/dev/null || :
%{_sbindir}/useradd -g %{rspamd_user} -c "Rspamd user" -s /bin/false -r -d %{_sharedstatedir}/%{name} %{rspamd_user} 2>/dev/null || :

%post
#Macro is not used as we want to do this on upgrade
#%%systemd_post %%{name}.service
systemctl --no-reload preset %{name}.service >/dev/null 2>&1 || :
%{__chown} %{rspamd_user}:%{rspamd_user}  %{_localstatedir}/log/%{name}

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
# TODO: Collect licenses from all bundled dependencies
%license %{_docdir}/licenses/LICENSE.md
%{_bindir}/*

%{_datadir}/%{name}

%dir %{_libdir}/%{name}
%{_libdir}/%{name}/*
%{_presetdir}/80-rspamd.preset
%{_mandir}/man1/rspamadm.*
%{_mandir}/man1/rspamc.*
%{_mandir}/man8/rspamd.*
%config(noreplace) %{_sysconfdir}/logrotate.d/rspamd
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/*.inc
%dir %{_sysconfdir}/%{name}/local.d
%dir %{_sysconfdir}/%{name}/modules.d
%dir %{_sysconfdir}/%{name}/override.d
%dir %{_sysconfdir}/%{name}/scores.d
%config(noreplace) %{_sysconfdir}/%{name}/modules.d/*
%config(noreplace) %{_sysconfdir}/%{name}/scores.d/*
%{_unitdir}/%{name}.service
%attr(-, %{rspamd_user}, %{rspamd_user}) %dir %{_sharedstatedir}/%{name}

%changelog
* Thu Oct 10 2019 Mark Verlinde <mark.verlinde@gmail.com> - 1.9.4-2.2
- conservative build for aarch64, fixes random segfaults

* Sat Oct 05 2019 Mark Verlinde <mark.verlinde@gmail.com> - 1.9.4-2.1
- switch to LorbusChris/rspamd-rpm repository
- apdoted for el7 arm and aarch64 build
- targeted to be functional compatible with upstream releases

* Fri Aug 02 2019 Felix Kaechele <heffer@fedoraproject.org> - 1.9.4-2
- remove fann BR, deprecated in favor of torch
- add gd support
- remove gmime BR, it's unused
- add libcurl, enables the use of UCL URL includes
- add openblas support for enhanced regex performance
- switch to pcre2 for enhanced regex performance
- drop some unused defines in the cmake call

* Sun Jul 28 2019 Christian Glombek <lorbus@fedoraproject.org> - 1.9.4-1
- Update to 1.9.4
- Keep versioned symlinks (Evan Klitzke)
- Run make_build macro in build section (Evan Klitzke)

* Wed Jan 30 2019 Ajay Ramaswamy <ajayr@krithika.net> - 1.8.3-2
- use proper macro for systemd preset file

* Thu Dec 20 2018 Christian Glombek <lorbus@fedoraproject.org> - 1.8.3-1
- Update to 1.8.3
- Use sysusers config and %%sysusers_create_package macro for user creation
- Added libunwind and jemalloc build dependencies
- Enabled builds for ppc arches without luajit availability
- Turned on testing during build
- Disabled install of service unit from upstream repo
- Manage local and shared state dirs with systemd service unit

* Wed Oct 31 2018 Mark Verlinde <mark.verlinde@gmail.com> 1.8.1-1
- Update to 1.8.1
- Cleanup specfile

* Wed Jul 04 2018 Mark Verlinde <mark.verlinde@gmail.com> 1.7.5-1
- Update to 1.7.7
- Aditional buildbequires luajit-devel libicu-devel
- Sanitized specfile for (centos) el7 build

# Third-party dependency notices

VoxEthos project-authored material is licensed under Apache-2.0 (see [`../LICENSE`](../LICENSE)). The dependencies below retain their own licenses; the project license does not replace those terms. No dependency source, wheel, compiled library, dataset, or model artifact is vendored in this repository.

## Backend runtime dependencies

| Package | Pinned version | License |
|---|---:|---|
| FastAPI | 0.162.2 | MIT |
| Starlette | 1.10.0 | BSD-3-Clause |
| Uvicorn (standard extra) | 0.34.0 | BSD-3-Clause |
| python-multipart | 0.0.33 | Apache-2.0 |
| Pydantic | 2.10.5 | MIT |
| NumPy | 2.2.2 | BSD-3-Clause |

Licenses were verified against the license files included in the pinned Python distributions. NumPy binary distributions can bundle components with additional notices, including OpenBLAS (BSD-3-Clause), LAPACK (BSD-3-Clause-Attribution), GCC's libgfortran runtime (GPL-3.0-with-GCC-exception), and libquadmath (LGPL-2.1-or-later), as well as other small components. Preserve the notices supplied with the selected NumPy distribution when redistributing binary artifacts. The backend requirements file pins direct dependencies but is not a complete transitive lockfile; audit each resolved environment.

## Frontend direct dependencies

| Package | Pinned version | License |
|---|---:|---|
| lucide-react | 1.25.0 | ISC |
| react | 19.2.8 | MIT |
| react-dom | 19.2.8 | MIT |
| @types/react | 19.2.17 | MIT |
| @types/react-dom | 19.2.3 | MIT |
| @vitejs/plugin-react | 6.0.3 | MIT |
| TypeScript | 7.0.2 | Apache-2.0 |
| Vite | 8.3.7 | MIT |

`frontend/package-lock.json` pins the transitive frontend dependency tree. The installed lock metadata exposed license metadata for all 27 package entries inspected; identifiers included Apache-2.0, BSD-3-Clause, ISC, MIT, and MPL-2.0. Review each upstream license when changing dependencies and preserve the lockfile.

## Development and test dependencies

| Package | Pinned version | License |
|---|---:|---|
| pytest | 9.0.3 | MIT |
| httpx2 | 2.16.0 | BSD-3-Clause |
| pip-audit | 2.9.0 | Apache-2.0 (PyPI OSI classifier; installed metadata has no explicit license field) |

Dependency metadata and manifests were inspected for this migration. Vulnerability-audit results are recorded separately by the verification run; a license identifier is not a security assessment or a grant of rights to data/models.
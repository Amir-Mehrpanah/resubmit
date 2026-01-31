Publishing `resubmit` via GitHub (recommended)

Steps to publish the package to PyPI using GitHub Actions (publish on tag push):

1. Create a PyPI API token
   - Log into https://pypi.org/ and go to your account -> API tokens -> Add token
   - Choose scope ("Upload project" or "Entire account") and create token
   - Copy the token (you'll need it once)

2. Add the token to your GitHub repository as a secret
   - Go to your repository -> Settings -> Secrets and variables -> Actions -> New repository secret
   - Name: `PYPI_API_TOKEN`
   - Value: (the token from PyPI)

3. Push your repository to GitHub
   - Create a repo on GitHub (e.g., `your-org/resubmit`) and push:
     - git remote add origin git@github.com:your-org/resubmit.git
     - git push -u origin main

7. Verify publication
   - Check https://pypi.org/project/resubmit/ for the new release

Notes
- Before publishing to the real PyPI you can test the flow using TestPyPI and a separate token (update the workflow to use TestPyPI endpoint). Ask me if you want that flow added.
- Keep your `PYPI_API_TOKEN` secret. Use GitHub repo secrets and do not commit the token anywhere.


for each change:

1. Bump version in `pyproject.toml`
   - Update `version = "x.y.z"` to the next release (semantic versioning is recommended)

2. Tag the release and push the tag
   - git tag vX.Y.Z
   - git push origin vX.Y.Z

3. GitHub Actions will trigger on the tag push
   - The workflow `publish.yml` will build the distribution and publish to PyPI using the `PYPI_API_TOKEN` secret
   - A GitHub Release will be created automatically (optional step in the workflow)
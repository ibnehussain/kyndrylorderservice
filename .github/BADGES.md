# GitHub Actions Status Badges

## How to Add CI Badge to README

Add this badge to your `README.md` to display the CI workflow status:

### Markdown Format
```markdown
[![CI](https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml/badge.svg)](https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml)
```

### HTML Format
```html
<a href="https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml">
  <img src="https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml/badge.svg" alt="CI">
</a>
```

### Badge for Specific Branch
```markdown
[![CI](https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml)
```

## Additional Recommended Badges

### Code Coverage (Codecov)
```markdown
[![codecov](https://codecov.io/gh/ibnehussain/kyndrylorderservice/branch/main/graph/badge.svg)](https://codecov.io/gh/ibnehussain/kyndrylorderservice)
```

### Python Version
```markdown
![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
```

### License
```markdown
![License](https://img.shields.io/badge/license-MIT-green)
```

### Code Style
```markdown
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## Complete Badge Section Example

Add this to the top of your README.md:

```markdown
# Order Management Service

[![CI](https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml/badge.svg)](https://github.com/ibnehussain/kyndrylorderservice/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ibnehussain/kyndrylorderservice/branch/main/graph/badge.svg)](https://codecov.io/gh/ibnehussain/kyndrylorderservice)
![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready RESTful API service for managing customer orders...
```

## Visual Preview

This will display as:

![CI](https://img.shields.io/badge/CI-passing-brightgreen)
![codecov](https://img.shields.io/badge/coverage-85%25-yellowgreen)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![Code style](https://img.shields.io/badge/code%20style-black-000000)

## Setup Instructions

1. **Copy the badge markdown** from above
2. **Paste it** at the top of your README.md (below the title)
3. **Commit and push** the changes
4. **Verify** the badge appears correctly on GitHub

The badge will automatically update based on the latest CI run status.

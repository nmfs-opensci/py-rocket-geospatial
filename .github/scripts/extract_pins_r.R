#!/usr/bin/env Rscript

# Generate a pinned install script for all packages installed in a given library.
#
# Usage:
#   Rscript .github/scripts/extract_pins_r.R <lib_path> <out_path>
#
# Example:
#   Rscript .github/scripts/extract_pins_r.R /usr/local/lib/R/site-library /work/packages-r-pinned.R
#
# Requirements:
# - Must run inside the container so getOption("repos")[1] reflects the image defaults.
# - Avoids \s escape issues by using [[:space:]]* in regex.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript extract_pins_r.R <lib_path> <out_path>", call. = FALSE)
}

lib_path <- args[[1]]
out_path <- args[[2]]

if (!dir.exists(lib_path)) {
  stop(sprintf("Library path does not exist: %s", lib_path), call. = FALSE)
}

pkgs <- installed.packages(lib.loc = lib_path)
repo <- getOption("repos")[1]

# Write to file
con <- file(out_path, open = "wt")
on.exit(close(con), add = TRUE)
sink(con)
on.exit(sink(), add = TRUE)

cat("#!/usr/bin/env Rscript\n")
cat("# Pinned R package installs\n")
cat("# Generated automatically from container image\n\n")
cat(sprintf('repo <- "%s"\n\n', repo))

# Small guardrail (keeps your earlier intent)
cat("# Guardrail: refuse to install to /home first libpath in container builds\n")
cat("install_lib <- .libPaths()[1]\n")
cat("if (grepl(\"^/home\", install_lib)) {\n")
cat("  stop(\"Error: Packages are being installed to /home. Exiting.\", call. = FALSE)\n")
cat("}\n\n")

for (i in seq_len(nrow(pkgs))) {
  pkg <- pkgs[i, "Package"]
  ver <- pkgs[i, "Version"]

  # Skip base/recommended
  priority <- pkgs[i, "Priority"]
  if (!is.na(priority) && priority %in% c("base", "recommended")) next

  desc_path <- file.path(lib_path, pkg, "DESCRIPTION")

  # If installed from GitHub, emit install_github line
  if (file.exists(desc_path)) {
    lines <- readLines(desc_path, warn = FALSE)

    remote_type <- grep("^RemoteType:", lines, value = TRUE)
    if (length(remote_type) > 0 && grepl("github", remote_type, ignore.case = TRUE)) {
      remote_username <- grep("^RemoteUsername:", lines, value = TRUE)
      remote_repo <- grep("^RemoteRepo:", lines, value = TRUE)
      remote_sha <- grep("^RemoteSha:", lines, value = TRUE)

      if (length(remote_username) > 0 && length(remote_repo) > 0) {
        username <- sub("^RemoteUsername:[[:space:]]*", "", remote_username)
        repo_name <- sub("^RemoteRepo:[[:space:]]*", "", remote_repo)

        if (length(remote_sha) > 0) {
          sha <- sub("^RemoteSha:[[:space:]]*", "", remote_sha)
          sha7 <- substr(sha, 1, 7)
          cat(sprintf('remotes::install_github("%s/%s@%s", upgrade = "never") # %s\n',
                      username, repo_name, sha7, ver))
        } else {
          cat(sprintf('remotes::install_github("%s/%s", upgrade = "never") # %s\n',
                      username, repo_name, ver))
        }
        next
      }
    }
  }

  # Otherwise, pin as CRAN version
  cat(sprintf('remotes::install_version("%s", version = "%s", repos = repo, upgrade = "never")\n',
              pkg, ver))
}

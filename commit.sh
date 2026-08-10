#!/bin/bash

# Commit chaque fichier modifié individuellement

git status --porcelain | while read -r status file; do
    # Ignore les fichiers supprimés
    if [[ "$status" == D* || "$status" == *D ]]; then
        continue
    fi

    git add "$file"
    git commit -m "[CG TRADUIT] $(basename "$file")"
done
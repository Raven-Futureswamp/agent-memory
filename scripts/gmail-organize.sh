#!/bin/bash
# Gmail Organizer - Labels emails into Plugin Distributions, Receipts, Activation Codes
export GOG_KEYRING_PASSWORD="raven2026"
export GOG_ACCOUNT="brownjeshua@gmail.com"

label_emails() {
    local LABEL="$1"
    local QUERY="$2"
    local TOTAL=0
    local ROUNDS=0
    local MAX_ROUNDS=${3:-50}

    echo ""
    echo "=========================================="
    echo "Labeling: $LABEL"
    echo "Query: $QUERY"
    echo "=========================================="

    while [ $ROUNDS -lt $MAX_ROUNDS ]; do
        # Get message IDs (using thread search for labeling)
        IDS=$(gog gmail messages search "$QUERY -label:\"$LABEL\"" --max 50 --plain 2>&1 | tail -n +2 | grep -v '^#' | awk -F'\t' '{print $1}')
        COUNT=$(echo "$IDS" | grep -c '[a-f0-9]')

        if [ "$COUNT" -eq 0 ]; then
            echo "No more messages for $LABEL."
            break
        fi

        # Add label to batch
        IDS_INLINE=$(echo "$IDS" | tr '\n' ' ')
        gog gmail batch modify $IDS_INLINE --add "$LABEL" --force --no-input 2>&1
        
        TOTAL=$((TOTAL + COUNT))
        ROUNDS=$((ROUNDS + 1))
        echo "Round $ROUNDS: Labeled $COUNT | Total: $TOTAL"
        
        sleep 1
    done

    echo "Done labeling $LABEL: $TOTAL messages"
}

echo "Starting Gmail Organization $(date)"

# === PLUGIN DISTRIBUTIONS ===
# Audio plugin companies and music software
label_emails "Plugin Distributions" \
    '{from:waves.com OR from:slatedigital.com OR from:native-instruments.com OR from:izotope.com OR from:fabfilter.com OR from:pluginalliance.com OR from:steinberg.net OR from:xlnaudio.com OR from:zynaptiq.com OR from:kazrog.com OR from:keepforest.com OR from:musehub.com OR from:mu.se OR from:moonbase.sh OR from:arturia.com OR from:soundtoys.com OR from:softube.com OR from:toontrack.com OR from:spectrasonics.net OR from:ujam.com OR from:output.com OR from:splice.com OR from:plugin-boutique.com OR from:sweetwater.com OR from:focusrite.com OR from:presonus.com OR from:ableton.com OR from:image-line.com}' \
    30

# === RECEIPTS ===
# Order confirmations, invoices, receipts
label_emails "Receipts" \
    '{subject:receipt OR subject:"order confirmation" OR subject:"your order" OR subject:invoice OR subject:"payment received" OR subject:"purchase confirmation" OR subject:"order shipped" OR subject:"shipping confirmation"} -category:promotions' \
    30

# === ACTIVATION CODES ===
# License keys, activation codes, serial numbers
label_emails "Activation Codes" \
    '{subject:activation OR subject:"license key" OR subject:"serial number" OR subject:"product key" OR subject:"registration code" OR subject:"download link" OR subject:"your license" OR subject:"activation code"}' \
    30

echo ""
echo "=========================================="
echo "Gmail Organization Complete $(date)"
echo "=========================================="

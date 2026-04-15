export default function PriceInfo({ result }) {
  const { card_name, card_set, card_number, price_low, price_mid, price_high, price_currency, estimated_psa_grade } = result;

  if (!card_name || card_name === "Unknown") {
    return (
      <div className="price-info price-info--unknown">
        <h3>Market Price</h3>
        <p className="price-unknown-msg">Could not identify this card. Try uploading a clearer image.</p>
      </div>
    );
  }

  const currency = price_currency || "USD";
  const fmt = (n) =>
    typeof n === "number" && n > 0
      ? n.toLocaleString("en-US", { style: "currency", currency, maximumFractionDigits: 0 })
      : "N/A";

  return (
    <div className="price-info">
      <h3>Market Price</h3>

      <div className="price-card-identity">
        <span className="price-card-name">{card_name}</span>
        {card_set && <span className="price-card-set">{card_set}</span>}
        {card_number && <span className="price-card-number">#{card_number}</span>}
        <span className="price-psa-badge">PSA {estimated_psa_grade}</span>
      </div>

      <div className="price-range-row">
        <div className="price-range-item price-low">
          <span className="price-range-label">Low</span>
          <span className="price-range-value">{fmt(price_low)}</span>
        </div>
        <div className="price-range-item price-mid">
          <span className="price-range-label">Mid</span>
          <span className="price-range-value">{fmt(price_mid)}</span>
        </div>
        <div className="price-range-item price-high">
          <span className="price-range-label">High</span>
          <span className="price-range-value">{fmt(price_high)}</span>
        </div>
      </div>

      <p className="price-disclaimer">
        Estimated prices based on AI market knowledge. Verify on PSA, eBay, or TCGPlayer before submitting.
      </p>
    </div>
  );
}

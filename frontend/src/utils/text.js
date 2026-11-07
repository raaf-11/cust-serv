export function fixRupeeSymbol(text) {
    return (text ?? "").replace(/■(?=\s?\d)/g, "₹");
}

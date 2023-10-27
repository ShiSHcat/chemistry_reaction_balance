import fetch from 'node-fetch';
const apiToken = "STITTOL1249122";

const balanceReaction = async (reaction) => {
    const url = `http://127.0.0.1:8000/balance_reaction?reaction=${encodeURIComponent(reaction)}}`;
    const response = await fetch(url, { method: 'POST' });
    const json = await response.json();
    return json;
}
export { balanceReaction };
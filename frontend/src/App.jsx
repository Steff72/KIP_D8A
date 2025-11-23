import { useCallback, useEffect, useMemo, useState } from "react";
import "./App.css";
import logo from "./assets/coin.png";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faWallet,
  faCoins,
  faSwimmingPool,
  faHammer,
  faPaperPlane,
  faAddressBook,
  faCopy,
} from "@fortawesome/free-solid-svg-icons";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

const formatHash = (hash, maxLength = 12) => {
  if (!hash) {
    return "—";
  }
  if (hash.length <= maxLength) {
    return hash;
  }
  return `${hash.slice(0, maxLength)}…`;
};

const formatTimestamp = (timestamp) => {
  if (timestamp === undefined || timestamp === null) {
    return "—";
  }

  const date = new Date(timestamp * 1000);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const CopyableAddress = ({ address, formatLen = 12 }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <span className="copyable-address">
      {formatHash(address, formatLen)}
      <button
        type="button"
        className="copy-button"
        onClick={handleCopy}
        title="Copy full address"
      >
        <FontAwesomeIcon icon={faCopy} className={copied ? "text-success" : ""} />
      </button>
    </span>
  );
};

function App() {
  const [walletInfo, setWalletInfo] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [chain, setChain] = useState([]);
  const [isMining, setIsMining] = useState(false);
  const [toast, setToast] = useState(null);
  const [showLatestBlockTx, setShowLatestBlockTx] = useState(false);
  const [formState, setFormState] = useState({ recipient: "", amount: "" });

  const latestBlock = chain.length > 0 ? chain[chain.length - 1] : null;

  const knownAddresses = useMemo(() => {
    const addresses = new Set();
    chain.forEach((block) => {
      if (!Array.isArray(block.data)) {
        return;
      }
      block.data.forEach((item) => {
        if (!item?.output) {
          return;
        }
        Object.keys(item.output).forEach((address) => {
          if (!address || address === walletInfo?.address) {
            return;
          }
          addresses.add(address);
        });
      });
    });
    return Array.from(addresses);
  }, [chain, walletInfo]);

  const fetchJson = useCallback(async (url, init) => {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(payload.message || "Request failed");
    }

    return response.json();
  }, []);

  const refreshWallet = useCallback(async () => {
    const payload = await fetchJson("/api/wallet/info");
    setWalletInfo(payload);
  }, [fetchJson]);

  const refreshTransactions = useCallback(async () => {
    const payload = await fetchJson("/api/transactions");
    setTransactions(payload.transactions || []);
  }, [fetchJson]);

  const refreshChain = useCallback(async () => {
    const payload = await fetchJson("/api/chain");
    setChain(payload.chain || []);
  }, [fetchJson]);

  useEffect(() => {
    refreshWallet();
    refreshTransactions();
    refreshChain();
    const intervalId = setInterval(() => {
      refreshWallet();
      refreshTransactions();
      refreshChain();
    }, 2000);

    return () => clearInterval(intervalId);
  }, [refreshChain, refreshTransactions, refreshWallet]);

  useEffect(() => {
    if (!toast) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timeoutId);
  }, [toast]);

  const handleSubmitTransaction = async (event) => {
    event.preventDefault();
    setToast(null);

    const amount = Number.parseInt(formState.amount, 10);
    if (!formState.recipient || Number.isNaN(amount) || amount <= 0) {
      setToast({
        type: "error",
        message: "Enter a valid recipient and an amount greater than zero.",
      });
      return;
    }

    try {
      await fetchJson("/api/transactions", {
        method: "POST",
        body: JSON.stringify({
          recipient: formState.recipient.trim(),
          amount,
        }),
      });
      await refreshTransactions();
      setToast({ type: "success", message: "Transaction broadcast successfully." });
      setFormState({ recipient: "", amount: "" });
    } catch (error) {
      setToast({ type: "error", message: error.message });
    }
  };

  const handleMineBlock = async () => {
    setIsMining(true);
    setToast(null);
    try {
      await fetchJson("/api/blocks", { method: "POST" });
      await Promise.all([refreshTransactions(), refreshWallet(), refreshChain()]);
      setToast({ type: "success", message: "New block mined." });
      setShowLatestBlockTx(false);
    } catch (error) {
      setToast({ type: "error", message: error.message });
    } finally {
      setIsMining(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__content">
          <img src={logo} alt="D8A Coin" className="app-logo" />
          <h1>D8A Coin Dashboard</h1>
        </div>
      </header>

      <main className="app-main">
        <section className="row">
          <article className="panel wallet-panel">
            <h2>
              My Wallet <FontAwesomeIcon icon={faWallet} />
            </h2>
            {walletInfo ? (
              <div className="wallet-panel__body">
                <p>
                  <span className="label">Address:</span>{" "}
                  <CopyableAddress address={walletInfo.address} formatLen={16} />
                </p>
                <p>
                  <span className="label">Balance:</span> {walletInfo.balance} DBA
                </p>
              </div>
            ) : (
              <p className="muted">Loading wallet details…</p>
            )}
          </article>

          <article className="panel send-panel">
            <h2>
              Make a Transaction <FontAwesomeIcon icon={faCoins} />
            </h2>
            <form className="send-form" onSubmit={handleSubmitTransaction}>
              <label htmlFor="recipient">Recipient</label>
              <input
                id="recipient"
                name="recipient"
                value={formState.recipient}
                onChange={(event) =>
                  setFormState((state) => ({ ...state, recipient: event.target.value }))
                }
                placeholder="Enter recipient address"
                autoComplete="off"
                spellCheck="false"
              />
              <label htmlFor="amount">Amount</label>
              <input
                id="amount"
                name="amount"
                type="number"
                min="1"
                value={formState.amount}
                onChange={(event) =>
                  setFormState((state) => ({ ...state, amount: event.target.value }))
                }
              />
              <button type="submit" className="button primary">
                Submit <FontAwesomeIcon icon={faPaperPlane} />
              </button>
            </form>
            <div className="known-addresses">
              <h3>
                Known Addresses <FontAwesomeIcon icon={faAddressBook} />
              </h3>
              {knownAddresses.length > 0 ? (
                <div className="known-addresses__list">
                  {knownAddresses.map((address) => (
                    <CopyableAddress key={address} address={address} formatLen={18} />
                  ))}
                </div>
              ) : (
                <p className="muted">None so far…</p>
              )}
            </div>
          </article>
        </section>

        <section className="row">
          <article className="panel pool-panel">
            <h2>
              Transaction Pool <FontAwesomeIcon icon={faSwimmingPool} />
            </h2>
            {transactions.length === 0 ? (
              <p className="muted">No open transactions.</p>
            ) : (
              <ul className="tx-list">
                {transactions.map((transaction) => {
                  const outputs = Object.entries(transaction.output || {}).filter(
                    ([address]) => address !== walletInfo?.address,
                  );
                  return (
                    <li key={transaction.id}>
                      <span className="tx-id">{formatHash(transaction.id, 14)}</span>
                      {outputs.map(([address, amount]) => (
                        <div key={address}>
                          <span className="label">To:</span>{" "}
                          <CopyableAddress address={address} formatLen={14} /> – {amount} DBA
                        </div>
                      ))}
                    </li>
                  );
                })}
              </ul>
            )}
            <button type="button" className="button" onClick={handleMineBlock} disabled={isMining}>
              {isMining ? "Mining…" : "Mine a new Block"}{" "}
              <FontAwesomeIcon icon={faHammer} />
            </button>
          </article>

          <article className="panel blockchain-panel">
            <h2>D8A Chain</h2>
            {latestBlock ? (
              <div className="block">
                <p>
                  <span className="label">Timestamp:</span> {formatTimestamp(latestBlock.timestamp)}
                </p>
                <p>
                  <span className="label">Prev Hash:</span> {formatHash(latestBlock.last_hash)}
                </p>
                <p>
                  <span className="label">Hash:</span> {formatHash(latestBlock.hash)}
                </p>
                <p>
                  <span className="label">Difficulty:</span> {latestBlock.difficulty}
                </p>
                <p>
                  <span className="label">Nonce:</span> {latestBlock.nonce}
                </p>

                <button
                  type="button"
                  className="button"
                  onClick={() => setShowLatestBlockTx((value) => !value)}
                >
                  {showLatestBlockTx ? "Hide Transactions" : "Show Transactions"}
                </button>

                {showLatestBlockTx ? (
                  <div className="block-transactions">
                    {Array.isArray(latestBlock.data) && latestBlock.data.length > 0 ? (
                      latestBlock.data.map((tx) => (
                        <div className="transaction" key={tx.id || tx.hash}>
                          <span className="tx-id">{formatHash(tx?.id || "reward", 14)}</span>
                          <div className="tx-outputs">
                            {Object.entries(tx?.output || {}).map(([address, amount]) => (
                              <span key={address}>
                                <CopyableAddress address={address} formatLen={14} /> → {amount}{" "}
                                DBA
                              </span>
                            ))}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="muted">No transactions in this block.</p>
                    )}
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="muted">Loading chain data…</p>
            )}
          </article>
        </section>
      </main>

      <footer className="app-footer">
        <p>D8A Coin • Mini blockchain experiment</p>
      </footer>

      {toast ? (
        <div className={`toast ${toast.type === "error" ? "toast--error" : "toast--success"}`}>
          {toast.message}
        </div>
      ) : null}
    </div>
  );
}

export default App;

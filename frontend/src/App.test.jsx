import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';

// Mock the environment variable
vi.stubGlobal('import.meta', { env: { VITE_API_BASE_URL: '' } });

// Mock fetch
global.fetch = vi.fn();

describe('App Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the dashboard header', async () => {
        fetch.mockResolvedValue({ ok: true, json: async () => ({}) });
        render(<App />);
        expect(screen.getByText(/D8A Coin Dashboard/i)).toBeInTheDocument();
    });

    it('displays wallet info', async () => {
        const mockWallet = { address: 'abc1234567890def', balance: 100 };
        fetch.mockImplementation((url) => {
            if (url.includes('/api/wallet/info')) {
                return Promise.resolve({ ok: true, json: async () => mockWallet });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) });
        });

        render(<App />);

        await waitFor(() => {
            expect(screen.getByText(/abc1234567890def/i)).toBeInTheDocument();
            expect(screen.getByText(/100 DBA/i)).toBeInTheDocument();
        });
    });

    it('displays transaction pool', async () => {
        const mockTx = {
            id: 'tx123',
            output: { 'recipient1': 50 }
        };
        fetch.mockImplementation((url) => {
            if (url.includes('/api/transactions')) {
                return Promise.resolve({ ok: true, json: async () => ({ transactions: [mockTx] }) });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) });
        });

        render(<App />);

        await waitFor(() => {
            expect(screen.getByText(/tx123/i)).toBeInTheDocument();
            expect(screen.getByText(/recipient1/i)).toBeInTheDocument();
            expect(screen.getByText(/50 DBA/i)).toBeInTheDocument();
        });
    });

    it('handles mining a block', async () => {
        fetch.mockImplementation((url) => {
            if (url.includes('/api/blocks') && url.includes('POST')) {
                return Promise.resolve({ ok: true, json: async () => ({ block: {} }) });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) });
        });

        render(<App />);

        const mineButton = screen.getByText(/Mine a new Block/i);
        fireEvent.click(mineButton);

        await waitFor(() => {
            expect(screen.getByText(/New block mined/i)).toBeInTheDocument();
        });
    });
    it('displays full address without truncation', async () => {
        const longAddress = 'verylongaddresscheckthatisnottruncated1234567890';
        const mockWallet = { address: longAddress, balance: 100 };
        fetch.mockImplementation((url) => {
            if (url.includes('/api/wallet/info')) {
                return Promise.resolve({ ok: true, json: async () => mockWallet });
            }
            return Promise.resolve({ ok: true, json: async () => ({}) });
        });

        render(<App />);

        await waitFor(() => {
            expect(screen.getByText(longAddress)).toBeInTheDocument();
        });
    });
});

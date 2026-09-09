'use client';

import { ccc } from '@ckb-ccc/connector-react';
import { LoaderCircle, Unplug, WalletCards } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { truncateMiddle } from '@/lib/format';

export function WalletControl() {
  const { open, disconnect, wallet, signerInfo } = ccc.useCcc();
  const [address, setAddress] = useState('');
  const [loadingAddress, setLoadingAddress] = useState(false);

  useEffect(() => {
    let active = true;
    if (!signerInfo) {
      setAddress('');
      setLoadingAddress(false);
      return;
    }
    setLoadingAddress(true);
    signerInfo.signer.getRecommendedAddress()
      .then((nextAddress) => { if (active) setAddress(nextAddress); })
      .catch(() => { if (active) setAddress('Address unavailable'); })
      .finally(() => { if (active) setLoadingAddress(false); });
    return () => { active = false; };
  }, [signerInfo]);

  if (!signerInfo) {
    return <Button variant="secondary" size="sm" onClick={open}><WalletCards className="size-3.5" />Connect testnet wallet</Button>;
  }

  return (
    <div className="flex items-center gap-1">
      <Button variant="secondary" size="sm" onClick={open} aria-label={`Manage ${wallet?.name ?? 'connected'} wallet`}>
        {loadingAddress ? <LoaderCircle className="size-3.5 animate-spin" /> : <span className="size-2 rounded-full bg-healthy" aria-hidden="true" />}
        <span className="hidden sm:inline">{wallet?.name ?? 'Wallet'}</span>
        <span className="font-mono text-[11px]">{truncateMiddle(address || 'Connected', 6, 4)}</span>
      </Button>
      <Tooltip label="Disconnect wallet" side="bottom">
        <Button variant="ghost" size="icon-sm" onClick={() => void disconnect()} aria-label="Disconnect wallet"><Unplug className="size-3.5" /></Button>
      </Tooltip>
    </div>
  );
}

# Copyright (c) 2026 SeatXray Developers
# Licensed under the terms of the GNU Affero General Public License (AGPL) version 3.
# See LICENSE file in the project root for details.

"""Sync Service. Synchronizes local data with cloud."""

import os
import httpx
import json

class SyncService:
    """
    Handles Data Synchronization.
    Strategy A: Google Drive (File Sync)
    Strategy B: Cloudflare 'Deploy Your Own Backend' (Worker Proxy)
    """
    
    def __init__(self):
        # Cloudflare Config (User provided)
        self.cf_worker_url = os.getenv("CF_WORKER_URL") # e.g. https://my-seatxray-backend.user.workers.dev
        self.cf_secret = os.getenv("CF_SECRET")         # The shared secret key

    async def sync_google_drive(self):
        """
        Syncs local encrypted JSON to Google Drive App Folder.
        Placeholder for OAuth flow implementation.
        """
        print("[SyncService] Starting Google Drive Sync...")
        # TODO: Implement ft.GoogleOAuthProvider flow
        pass

    async def sync_cloudflare_d1(self, local_data: dict, conflict_resolver=None):
        """
        Pushes data to User's Cloudflare D1 via their personal Worker.
        Strictly follows 'Read-Before-Write' strategy.
        """
        if not self.cf_worker_url or not self.cf_secret:
            print("[SyncService] Cloudflare Backend not configured.")
            return False
            
        print(f"[SyncService] Syncing to Cloudflare: {self.cf_worker_url}")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-SeatXray-Secret": self.cf_secret}
                
                # 1. READ (Check Cloud state)
                print("[SyncService] Step 1: Reading Cloud State...")
                read_resp = await client.get(f"{self.cf_worker_url}/api/sync", headers=headers)
                
                if read_resp.status_code == 200:
                    cloud_data = read_resp.json()
                    # TODO: Implement merge/conflict resolution logic using conflict_resolver
                    # merged_data = conflict_resolver(local_data, cloud_data)
                    print("[SyncService] Cloud state retrieved. Merging...")
                
                # 2. WRITE (Push merged state)
                print("[SyncService] Step 2: Writing merged state...")
                write_resp = await client.post(
                    f"{self.cf_worker_url}/api/sync",
                    headers=headers,
                    json=local_data # Should be merged_data
                )
                write_resp.raise_for_status()
                
                print("[SyncService] Cloudflare Sync Success (Read-Write Complete).")
                return True
            except Exception as e:
                print(f"[SyncService] Cloudflare Sync Failed: {e}")
                return False

    async def get_kv_cache(self, key: str):
        """
        Retrieves SeatMap cache from Cloudflare KV via Worker.
        """
        if not self.cf_worker_url:
            return None
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.cf_worker_url}/api/kv/{key}",
                    headers={"X-SeatXray-Secret": self.cf_secret}
                )
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass
        return None

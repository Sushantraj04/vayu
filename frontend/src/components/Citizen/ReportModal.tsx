import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Camera, ShieldCheck, MapPin, Upload, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../../lib/api';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useTranslation();

  const [lat, setLat] = useState<number>(28.6139);
  const [lon, setLon] = useState<number>(77.2090);
  const [category, setCategory] = useState<string>('smoke');
  const [userPm25, setUserPm25] = useState<string>('');
  const [consent, setConsent] = useState<boolean>(true);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<any | null>(null);

  if (!isOpen) return null;

  // Approximate 500m grid rounding preview
  const previewLat = Math.round(lat / 0.005) * 0.005;
  const previewLon = Math.round(lon / 0.005) * 0.005;

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(pos.coords.latitude);
          setLon(pos.coords.longitude);
        },
        () => {
          // If denied, keep default Delhi center
          setErrorMsg('Location access denied. Using corridor center coordinates.');
        }
      );
    }
  };

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consent) {
      setErrorMsg('Mandatory consent is required to plot on public map.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      if (photoFile) {
        // Multipart form submission for image evidence
        const formData = new FormData();
        formData.append('latitude', lat.toString());
        formData.append('longitude', lon.toString());
        formData.append('category', category);
        if (userPm25) formData.append('user_pm25', userPm25);
        formData.append('consent', 'true');
        formData.append('photo', photoFile);

        const res = await api.submitReportForm(formData);
        setSuccessData(res);
      } else {
        // Pure JSON submission
        const res = await api.submitReportJSON({
          latitude: lat,
          longitude: lon,
          category,
          user_pm25: userPm25 ? parseFloat(userPm25) : undefined,
          consent: true,
        });
        setSuccessData(res);
      }

      if (onSuccess) onSuccess();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit citizen report.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-800/40">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100">Report Pollution Incident</h3>
              <p className="text-xs text-slate-400">Crowdsourced Ground Intelligence (DPG)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success View */}
        {successData ? (
          <div className="p-6 text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <h4 className="text-lg font-bold text-slate-100">Report Successfully Submitted</h4>
            <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700 text-xs text-left space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Tracking Public ID:</span>
                <span className="font-mono font-bold text-teal-400">{successData.public_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Privacy Anonymized Grid:</span>
                <span className="font-mono text-slate-200">
                  {successData.public_lat}, {successData.public_lon} (~500m cell)
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Satellite Cross-Validation:</span>
                <span className={`font-semibold ${successData.is_satellite_verified ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {successData.is_satellite_verified ? '✓ Verified by Active Fire Radiometry' : 'Queued for Analyst Review'}
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-400">
              Your report is now contributing to our regional airshed model without exposing your private residence location.
            </p>
            <button
              onClick={onClose}
              className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-500 text-white font-medium text-sm rounded-lg transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          /* Submission Form */
          <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
            {errorMsg && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Category */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Incident Category *
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="smoke">Crop Residue / Stubble Burning</option>
                <option value="industrial">Industrial Emissions / Factory Smoke</option>
                <option value="open_burning">Open Garbage / Waste Combustion</option>
                <option value="dust">Construction Dust / Unpaved Road Smog</option>
                <option value="other">Other High-Smoke Anomaly</option>
              </select>
            </div>

            {/* Location & Privacy Preview */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Incident Coordinates *
                </label>
                <button
                  type="button"
                  onClick={handleGetLocation}
                  className="text-[11px] text-teal-400 hover:underline flex items-center gap-1"
                >
                  <MapPin className="w-3 h-3" />
                  <span>Use Device GPS</span>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  step="0.0001"
                  value={lat}
                  onChange={(e) => setLat(parseFloat(e.target.value))}
                  placeholder="Latitude"
                  required
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-100"
                />
                <input
                  type="number"
                  step="0.0001"
                  value={lon}
                  onChange={(e) => setLon(parseFloat(e.target.value))}
                  placeholder="Longitude"
                  required
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-100"
                />
              </div>

              {/* Privacy by Design Indicator */}
              <div className="mt-2 p-2.5 rounded-lg bg-teal-500/10 border border-teal-500/20 text-[11px] text-teal-300 flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 shrink-0 text-teal-400 mt-0.5" />
                <div>
                  <strong>Privacy by Design:</strong> Coordinates will be rounded to{' '}
                  <span className="font-mono text-white">
                    {previewLat.toFixed(3)}, {previewLon.toFixed(3)}
                  </span>{' '}
                  (~500m grid cell) to safeguard personal address privacy on public feeds.
                </div>
              </div>
            </div>

            {/* Optional Sensor Reading */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Low-Cost Sensor PM2.5 (optional ug/m3)
              </label>
              <input
                type="number"
                step="0.1"
                value={userPm25}
                onChange={(e) => setUserPm25(e.target.value)}
                placeholder="e.g. 145.0"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-100 placeholder:text-slate-500"
              />
            </div>

            {/* Photo Evidence Upload */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Photo Evidence (EXIF metadata will be stripped automatically)
              </label>
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-4 text-center hover:border-slate-500 transition-colors cursor-pointer relative">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handlePhotoSelect}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                {photoPreview ? (
                  <div className="relative inline-block">
                    <img
                      src={photoPreview}
                      alt="Preview"
                      className="max-h-32 rounded-lg object-contain mx-auto"
                    />
                    <span className="text-[10px] text-emerald-400 block mt-1">
                      ✓ Image ready for EXIF sanitization
                    </span>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <Upload className="w-6 h-6 text-slate-400 mx-auto" />
                    <div className="text-xs text-slate-300">Click or drag image to attach</div>
                    <div className="text-[10px] text-slate-500">Max 5MB (JPEG, PNG, WebP)</div>
                  </div>
                )}
              </div>
            </div>

            {/* Public Mapping Consent */}
            <label className="flex items-start gap-2.5 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 rounded bg-slate-800 border-slate-700 text-teal-500 focus:ring-0 w-4 h-4"
              />
              <span className="text-xs text-slate-300">
                I agree to share this anonymized incident observation as a Digital Public Good to aid clean air monitoring.
              </span>
            </label>

            {/* Submit CTA */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting || !consent}
                className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold text-sm rounded-lg transition-colors shadow-lg shadow-teal-900/30 flex items-center justify-center gap-2"
              >
                {isSubmitting ? 'Sanitizing & Submitting...' : 'Submit Incident Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
